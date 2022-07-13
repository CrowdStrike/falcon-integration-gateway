# import traceback
import boto3
from botocore.exceptions import ClientError
# import json
from ...config import config
from ...log import log


class Submitter():
    def __init__(self, event):
        self.event = event
        self.ingestion_channel_id = config.get('cloudtrail_lake', 'ingestion_channel_id')
        self.role_arn = config.get('cloudtrail_lake', 'role_arn')
        self.account_id = config.get('cloudtrail_lake', 'account_id')

    # Map event into Open Audit Event format
    def open_audit_event(self):
        uid = self.event.original_event.uid
        event = self.event.original_event['event']
        metadata = self.event.original_event['metadata']
        event_time = self.event.time.isoformat(timespec='seconds') + 'Z'

        user_identity = {
            "type": metadata['eventType'],
            "principleId": event['UserId'],
            "details": {"AuditKeyValues": "empty"}
        }

        # Not all events have AuditKeyValues
        if self.event.audit_key_values:
            user_identity['details']['AuditKeyValues'] = event['AuditKeyValues']

        event_data = {
            "version": metadata['version'],
            "userIdentity": user_identity,
            "userAgent": "falcon-integration-gateway",
            "eventSource": "CrowdStrike",
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

    @staticmethod
    def send_to_cloudtraillake(event_data, ingestion_channel_id):
        client = boto3.client('cloudtraildata', region_name=config.get('cloudtrail_lake', 'region'))
        response = False
        try:
            response = client.put_audit_events(
                auditEvents=[
                    {
                        'id': 'NOT SURE YET',
                        'eventData': event_data
                    },
                ],
                ingestionChannelArn=ingestion_channel_id
            )
        except ClientError as err:
            log.exception(str(err))

        return response

    def submit(self):
        log.info("Processing user activity event: %s", self.event.original_event['event']['OperationName'])
        event_data = self.open_audit_event()
        ingestion_channel_id = self.ingestion_channel_id
        response = self.send_to_cloudtraillake(event_data, ingestion_channel_id)

        # Check response for errors
        if not response:
            log.error("Exception Error occured while sending event to CloudTrail Lake.")
        else:
            if response['failed']:
                log.error("Failed Response recieved for: %s", response['failed'])
            else:
                log.info("Successfully sent event to CloudTrail Lake. (Event ID: %s)", response['successful']['id'])

        # print(json.dumps(self.open_audit_event(), indent=4))
        # print(self.open_audit_event())


class Runtime():
    RELEVANT_EVENT_TYPES = ['AuthActivityAuditEvent']

    def __init__(self):
        log.info("AWS CloudTrail Lake Backend is enabled.")

    # def is_relevant(self, falcon_event):
    #     if falcon_event.service_name.lower() == "crowdstrike authentication":
    #         log.info(vars(falcon_event))
    #         print()
    #         return True
    #     return False

    def is_relevant(self, falcon_event):
        return falcon_event.service_name.lower() == "crowdstrike authentication"

    def process(self, falcon_event):
        Submitter(falcon_event).submit()


__all__ = ['Runtime']
