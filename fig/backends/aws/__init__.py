import json
from datetime import datetime
import boto3
from ...config import config
from ...log import log


class Submitter():
    def __init__(self, queue, event):
        self.sqs_queue = queue
        self.event = event

    def submit(self):
        log.info("Processing detection: %s", self.event.detect_description)
        sqs_payload = self.create_payload()
        response = self.sqs_queue.send_message(MessageBody=json.dumps(sqs_payload))
        log.info(
            'Detection found that meets severity threshold, sending to SQS. (SQS Message ID: %s)', str(
                response.get("MessageId")))

    def create_payload(self):
        payload = {
            "hostname": self.event.device_details["hostname"],
            "instance_id": self.event.instance_id,
            "service_provider_account_id": self.event.cloud_provider_account_id,
            "local_ip": self.event.device_details["local_ip"],
            "mac_address": self.event.device_details["mac_address"],
            "detected_mac_address": self.event.original_event["event"]["MACAddress"],
            "detected_local_ip": self.event.original_event["event"]["LocalIP"],
            "detection_id": self.event.event_id,
            "tactic": self.event.original_event["event"]["Tactic"],
            "technique": self.event.original_event["event"]["Technique"],
            "description": self.event.detect_description,
            "source_url": self.event.falcon_link,
            "generator_id": "Falcon Host",
            "types": ["Namespace: Threat Detections"],
            "created_at": self.event.time,
            "updated_at": ((datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))).isoformat() + 'Z'),
            "record_state": "ACTIVE",
            "severity": self.event.severity}
        try:
            payload["Process"] = {}
            payload["Process"]["Name"] = self.event.original_event["event"]["FileName"]
            payload["Process"]["Path"] = self.event.original_event["event"]["FilePath"]
        except KeyError:
            payload.pop("Process", None)

        try:
            payload['Network'] = self.network_payload()
        except KeyError:
            pass

        return payload

    def network_payload(self):
        net = {}
        net['Direction'] = \
            "IN" if self.event.original_event['event']['NetworkAccesses'][0]['ConnectionDirection'] == 0 else 'OUT'
        net['Protocol'] = self.event.original_event['event']['NetworkAccesses'][0]['Protocol']
        net['SourceIpV4'] = self.event.original_event['event']['NetworkAccesses'][0]['LocalAddress']
        net['SourcePort'] = self.event.original_event['event']['NetworkAccesses'][0]['LocalPort']
        net['DestinationIpV4'] = self.event.original_event['event']['NetworkAccesses'][0]['RemoteAddress']
        net['DestinationPort'] = self.event.original_event['event']['NetworkAccesses'][0]['RemotePort']
        return net


class Runtime():
    def __init__(self):
        log.info("AWS Backend is enabled.")
        try:
            aws_client = boto3.resource('sqs', region_name=config.get('aws', 'region'))
            self.queue = aws_client.get_queue_by_name(QueueName=config.get('aws', 'sqs_queue_name'))
        except BaseException:  # pylint: disable=W0703
            log.exception("Cannot configure AWS SQS Queue")
            self.queue = None
            raise

    def is_relevant(self, falcon_event):  # pylint: disable=R0201
        return falcon_event.cloud_provider == 'AWS_EC2'

    def process(self, falcon_event):  # pylint: disable=R0201
        Submitter(self.queue, falcon_event).submit()


__all__ = ['Runtime']
