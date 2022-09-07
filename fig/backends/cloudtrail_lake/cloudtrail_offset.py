import threading
import boto3
from botocore.exceptions import ClientError
from ...log import log


_offset_lock = threading.Lock()


class LastEventOffset():
    '''
    Manage the state of the last seen offset for each feed with SSM paramater store.
    This is used to determine where to start the next query for each feed upon init/restart
    to prevent duplicate events.
    '''
    def __init__(self):
        self.last_seen_offsets = {}
        self.param_name = 'last_seen_offsets'
        self.client = boto3.client('ssm')
        # Ensure SSM parameter exists
        self.validate_ssm_parameter()

    def validate_ssm_parameter(self):
        '''
        Ensure the SSM parameter exists.
        '''
        try:
            self.client.get_parameter(Name=self.param_name)
        except ClientError as err:
            if err.response['Error']['Code'] == 'ParameterNotFound':
                log.info("SSM parameter %s does not exist. Creating...", self.param_name)
                self.client.put_parameter(
                    Name=self.param_name,
                    Value='{}',
                    Type='String',
                    Overwrite=True
                )
            else:
                log.exception(str(err))

    def get_last_seen_offsets(self):
        '''
        Get the last seen offset for each feed.
        '''
        try:
            response = self.client.get_parameter(Name=self.param_name)
            last_seen_offsets = eval(response['Parameter']['Value'])
        except ClientError as err:
            log.exception("Failed to get last seen offset with error: %s", str(err))
        return last_seen_offsets

    def update_last_seen_offsets(self, feed_id, offset):
        '''
        Update the last seen offset for a given feed.
        '''
        try:
            _offset_lock.acquire()
            self.last_seen_offsets = self.get_last_seen_offsets()
            if offset > self.last_seen_offsets.get(feed_id, 0):
                self.last_seen_offsets[feed_id] = offset
                self.client.put_parameter(
                    Name=self.param_name,
                    Value=str(self.last_seen_offsets),
                    Type='String',
                    Overwrite=True
                )
                log.info("Updated last seen offset for feed %s to %s", feed_id, offset)
        except ClientError as err:
            log.exception("Failed to update last seen offset with error: %s", str(err))
        finally:
            _offset_lock.release()

        # with _offset_lock:
        #     self.last_seen_offsets[feed_id] = offset
        #     if self.last_seen_offsets[feed_id] > self.get_last_seen_offsets().get(feed_id, 0):
        #         try:
        #             self.client.put_parameter(
        #                 Name=self.param_name,
        #                 Value=str(self.last_seen_offsets),
        #                 Type='String',
        #                 Overwrite=True
        #             )
        #             log.info("Updated last seen offset for feed %s to %s", feed_id, offset)
        #         except ClientError as err:
        #             log.exception("Failed to update last seen offset with error: %s", str(err))
