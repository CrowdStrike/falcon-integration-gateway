from json import dumps
import boto3
from botocore.exceptions import ClientError
from ...config import config
from ...log import log
from .cloudtrail_offset import LastEventOffset


class Submitter():
    def __init__(self, event, channel_arn, region, account_id, last_event_offset):
        self.event = event
        self.channel_arn = channel_arn
        self.region = region
        self.account_id = account_id
        self.last_event_offset = last_event_offset

    def cloudtrail_lake_audit_event(self):
        '''
        Map the audit event and return a dict of the data.
        '''
        uid = self.event.original_event.uid
        event = self.event.original_event['event']
        metadata = self.event.original_event['metadata']
        event_time = self.event.time.isoformat(timespec='seconds') + 'Z'

        user_identity = {
            "type": metadata['eventType'],
            "principalId": event['UserId'],
            "details": {"AuditKeyValues": "n/a"}
        }

        # Not all events have AuditKeyValues
        if self.event.audit_key_values:
            user_identity['details']['AuditKeyValues'] = event['AuditKeyValues']

        event_data = {
            "version": metadata['version'],
            "userIdentity": user_identity,
            "userAgent": "falcon-integration-gateway",
            "eventSource": "crowdstrike",
            "eventName": event['OperationName'],
            "eventTime": event_time,
            "UID": uid,
            "sourceIPAddress": event['UserIp'],
            "recipientAccountId": self.account_id,
            "additionalEventData": {
                "raw": self.event.original_event
            }
        }

        return event_data

    def send_to_cloudtraillake(self, event_data):
        '''
        Sends the event to CloudTrail Lake. Returns the response.
        '''
        client = boto3.client('cloudtrail-data', region_name=self.region)
        response = False
        try:
            response = client.put_audit_events(
                auditEvents=[
                    {
                        'id': event_data['UID'],
                        'eventData': dumps(event_data)
                    }
                ],
                channelArn=self.channel_arn
            )
        except ClientError as err:
            log.exception(str(err))

        return response

    def submit(self):
        '''
        Submit events to CloudTrail Lake and updates the last seen offset.
        '''
        operation_name = self.event.original_event['event']['OperationName']
        uid = self.event.original_event.uid
        log.info("Processing user activity event: %s ID: %s", operation_name, uid)

        event_data = self.cloudtrail_lake_audit_event()
        response = self.send_to_cloudtraillake(event_data)

        # Check response for errors
        if not response:
            log.error("Exception Error occured while sending event to CloudTrail Lake.")
        else:
            if response['failed']:
                log.error("Failed Response recieved for: %s", response['failed'])
            else:
                log.info("Successfully sent event ID: %s to CloudTrail Lake. (Request ID: %s)",
                         uid, response['ResponseMetadata']['RequestId'])
                # Update the last seen offset for this feed
                self.last_event_offset.update_last_seen_offsets(self.event.original_event.feed_id,
                                                                self.event.original_event.offset)


class Runtime():
    RELEVANT_EVENT_TYPES = ['AuthActivityAuditEvent']

    def __init__(self):
        log.info("AWS CloudTrail Lake Backend is enabled.")
        # Initialize Config Variables
        self.channel_arn = config.get('cloudtrail_lake', 'channel_arn')
        self.region = config.get('cloudtrail_lake', 'region')
        self.account_id = None
        try:
            self.account_id = self.channel_arn.split(':')[4]
        except IndexError:
            log.error("Could not get account ID from Channel ARN: %s", self.channel_arn)
            raise
        # Instantiate the last seen offset object
        self.last_event_offset = LastEventOffset()
        # Get the last seen offset for each feed
        self.last_seen_offsets = self.last_event_offset.get_last_seen_offsets()

    def is_relevant(self, falcon_event):
        if falcon_event.service_name.lower() != "crowdstrike authentication":
            return False

        feed_id = falcon_event.original_event.feed_id
        offset = falcon_event.original_event.offset
        if offset > self.last_seen_offsets.get(feed_id, 0):
            return True
        return False

    def process(self, falcon_event):
        Submitter(falcon_event, self.channel_arn, self.region, self.account_id, self.last_event_offset).submit()


__all__ = ['Runtime']
