import json
from functools import lru_cache
import boto3
from botocore.exceptions import ClientError
from ...config import config
from ...log import log


class Submitter():
    def __init__(self):
        aws_region = config.get('aws_sqs', 'region')
        log.debug("Attempting to connect to AWS (region %s) SQS: %s", aws_region, self.sqs_queue_name)
        try:
            aws_client = boto3.resource('sqs', region_name=aws_region)
            self.queue = aws_client.get_queue_by_name(QueueName=self.sqs_queue_name)
        except ClientError:  # pylint: disable=W0703
            log.exception("Cannot configure AWS SQS Queue: %s in %s", aws_region, self.sqs_queue_name)
            self.queue = None
            raise

    def submit(self, event):
        eoe = event.original_event
        if self.is_fifo:
            feed_id = getattr(eoe, 'feed_id') if hasattr(eoe, 'feed_id') else 0
            self.queue.send_message(
                MessageGroupId="fig/%s/%s" % (self.app_id, feed_id),
                MessageDeduplicationId=str(eoe.offset),
                MessageBody=json.dumps(eoe)
            )
        else:
            self.queue.send_message(MessageBody=json.dumps(eoe))

    @property
    @lru_cache
    def is_fifo(self):
        return self.sqs_queue_name.endswith('.fifo')

    @property
    @lru_cache
    def sqs_queue_name(self):
        return config.get('aws_sqs', 'sqs_queue_name')

    @property
    @lru_cache
    def app_id(self):
        return config.get('falcon', 'application_id')


class Runtime():
    RELEVANT_EVENT_TYPES = "ALL"

    def __init__(self):
        log.info("AWS SQS Backend is enabled.")
        self.submitter = Submitter()

    def is_relevant(self, falcon_event):
        return True

    def process(self, falcon_event):
        self.submitter.submit(falcon_event)


__all__ = ['Runtime']
