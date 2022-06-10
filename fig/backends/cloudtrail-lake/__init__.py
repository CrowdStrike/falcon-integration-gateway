from asyncio import events
from datetime import datetime
import traceback
import boto3
from botocore.exceptions import ClientError
from ...config import config
from ...log import log

class Submitter():
    def __init__(self, event):
        self.event = events


class Runtime():
    RELEVANT_EVENT_TYPES = ['AuthActivityAuditEvent']

    def __init__(self):
        log.info("AWS CloudTrail Lake Backend is enabled.")

    def is_relevant(self, falcon_event):
        return falcon_event.cloud_provider == 'AWS_EC2'

    # def process(self, falcon_event):
    #     Submitter(falcon_event).submit()


__all__ = ['Runtime']
