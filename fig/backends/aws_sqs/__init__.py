import json
import boto3
from botocore.exceptions import ClientError
from ...config import config
from ...log import log


class Submitter():
    def __init__(self):
        aws_region = config.get('aws_sqs', 'region')
        sqs_queue_name = config.get('aws_sqs', 'sqs_queue_name')
        log.debug("Attempting to connect to AWS (region %s) SQS: %s", aws_region, sqs_queue_name)
        try:
            aws_client = boto3.resource('sqs', region_name=aws_region)
            self.queue = aws_client.get_queue_by_name(QueueName=sqs_queue_name)
        except ClientError:  # pylint: disable=W0703
            log.exception("Cannot configure AWS SQS Queue: %s in %s", aws_region, sqs_queue_name)
            self.queue = None
            raise

    def submit(self, event):
        self.queue.send_message(MessageBody=json.dumps(event.original_event))


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
