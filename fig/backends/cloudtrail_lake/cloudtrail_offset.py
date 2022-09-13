import ast
import threading
import boto3
from botocore.exceptions import ClientError
from ...config import config
from ...log import log


_offset_lock = threading.RLock()


class LastEventOffset():
    '''
    Manage the state of the last seen offset for each feed with SSM paramater store.
    This is used to determine where to start the next query for each feed upon init/restart
    to prevent duplicate events.
    '''
    def __init__(self):
        self.last_seen_offsets = {}
        self.param_name = 'last_seen_offsets'
        self.client = boto3.client('ssm', region_name=config.get('cloudtrail_lake', 'region'))
        self.validate_ssm_parameter()
        self.cache = None

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
                raise err

    def get_last_seen_offsets(self):
        '''
        Get the last seen offset for all feeds via local cache or SSM parameter store.
        '''
        with _offset_lock:
            if self.cache is None:
                self.cache = self._get_remote()
            return self.cache

    def update_last_seen_offsets(self, feed_id, offset):
        '''
        Update the last seen offset for a given feed.
        '''
        with _offset_lock:
            if self.get_last_seen_offsets().get(feed_id, 0) < offset:
                self.cache[feed_id] = offset
                self._put_remote(self.cache)
                log.info("Updated last seen offset for stream feed: %s to: %s", feed_id, offset)

    def _put_remote(self, value):
        '''
        Put a value to the SSM parameter store.
        '''
        try:
            self.client.put_parameter(
                Name=self.param_name,
                Value=str(value),
                Type='String',
                Overwrite=True
            )
        except ClientError as err:
            log.exception("Failed to put value to SSM parameter with error: %s", str(err))

    def _get_remote(self):
        '''
        Get a value from the SSM parameter store.
        '''
        try:
            response = self.client.get_parameter(Name=self.param_name)
            return ast.literal_eval(response['Parameter']['Value'])
        except ClientError as err:
            log.exception("Failed to get value from SSM parameter with error: %s", str(err))
            return {}
