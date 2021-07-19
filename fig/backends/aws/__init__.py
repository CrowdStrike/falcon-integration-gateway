from datetime import datetime
import boto3
import traceback
from ...config import config
from ...log import log
from botocore.exceptions import ClientError


class Submitter():
    def __init__(self, event):
        self.event = event

    def find_instance(self, instance_id, mac_address):
        # Instance IDs are unique to the region, not the account, so we have to check them all

        ec2_client = boto3.client("ec2")
        regions = [region["RegionName"] for region in ec2_client.describe_regions()["Regions"]]
        for region in regions:
            ec2 = boto3.resource("ec2", region_name=region)
            try:
                ec2instance = ec2.Instance(instance_id)
                found = False
                # Confirm the mac address matches
                for iface in ec2instance.network_interfaces:
                    det_mac = mac_address.lower().replace(":", "").replace("-", "")
                    ins_mac = iface.mac_address.lower().replace(":", "").replace("-", "")
                    if det_mac == ins_mac:
                        found = True
                if found:
                    break
                else:
                    ec2instance = False
            except ClientError:
                continue
            except Exception:
                tb = traceback.format_exc()
                log.error(str(tb))
                continue

        return ec2instance

    def sendToSecurityHub(self, manifest):
        client = boto3.client('securityhub', region_name=config.get('aws', 'region'))
        check_response = {}
        found = False
        try:
            check_response = client.get_findings(Filters={'Id': [{'Value': manifest["Id"], 'Comparison': 'EQUALS'}]})
            for finding in check_response["Findings"]:
                found = True
        except Exception:
            pass

        import_response = False
        if not found:
            try:
                import_response = client.batch_import_findings(Findings=[manifest])
            except ClientError as err:
                # Boto3 issue communicating with SH, throw the error in the log
                log.error(str(err))
            except Exception:
                # Unknown error / issue, log the result
                tb = traceback.format_exc()
                log.error(str(tb))

        return import_response

    def submit(self):
        log.info("Processing detection: %s", self.event.detect_description)
        sh_payload = self.create_payload()
        send = False
        if self.event.instance_id:
            instance = self.find_instance(self.event.instance_id, self.event.device_details["mac_address"])
            try:
                for iface in instance.network_interfaces:
                    # Only send alerts for instances we can find
                    send = True

            except ClientError:
                # Not our instance
                i_id = self.event.instance_id
                mac = self.event.device_details["mac_address"]
                log.info(f"Instance {i_id} with MAC address {mac} not found in regions searched. Alert not processed.")

        if send:
            response = self.sendToSecurityHub(sh_payload)
            if not response:
                log.info("Detection already submitted to Security Hub. Alert not processed.")
            else:
                if response["SuccessCount"] > 0:
                    submit_msg = f"Detection submitted to Security Hub. (Request ID: {response['ResponseMetadata']['RequestId']})"
                    log.info(submit_msg)

    def create_payload(self):
        region = config.get('aws', 'region')
        accountID = boto3.client("sts").get_caller_identity().get('Account')
        severityProduct = self.event.severity_value
        severityNormalized = severityProduct * 20
        payload = {
            "SchemaVersion": "2018-10-08",
            "ProductArn": "arn:aws:securityhub:{}:517716713836:product/crowdstrike/crowdstrike-falcon".format(region),
            "AwsAccountId": accountID,
            "SourceUrl": self.event.falcon_link,
            "GeneratorId": "Falcon Host",
            "CreatedAt": datetime.utcfromtimestamp(float(self.event.event_create_time) / 1000.).isoformat() + 'Z',
            "UpdatedAt": ((datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))).isoformat() + 'Z'),
            "RecordState": "ACTIVE",
            "Severity": {"Product": severityProduct, "Normalized": severityNormalized}
        }

        # Instance ID based detail
        if self.event.instance_id:
            payload["Id"] = f"{self.event.instance_id}{self.event.event_id}"
            payload["Title"] = "Falcon Alert. Instance: %s" % self.event.instance_id
            payload["Resources"] = [{"Type": "AwsEc2Instnace", "Id": self.event.instance_id, "Region": region}]
        else:
            payload["Id"] = f"UnknownInstanceID:{self.event.event_id}"
            payload["Title"] = "Falcon Alert"
            payload["Resources"] = [{"Type": "Other",
                                     "Id": f"UnknownInstanceId:{self.event.event_id}",
                                     "Region": region
                                     }]
        # Description
        aws_id = ""
        if self.event.cloud_provider_account_id:
            aws_id = f"| AWS Account for alerting instance: {self.event.cloud_provider_account_id}"
        payload["Description"] = f"{self.event.detect_description} {aws_id}"

        # TTPs
        try:
            payload["Types"] = ["Namespace: TTPs",
                                "Category: %s" % self.event.original_event["event"]["Tactic"],
                                "Classifier: %s" % self.event.original_event["event"]["Technique"]
                                ]
        except KeyError:
            payload.pop("Types", None)

        # Running process detail
        try:
            payload["Process"] = {}
            payload["Process"]["Name"] = self.event.original_event["event"]["FileName"]
            payload["Process"]["Path"] = self.event.original_event["event"]["FilePath"]
        except KeyError:
            payload.pop("Process", None)

        # Network detail
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

    def is_relevant(self, falcon_event):  # pylint: disable=R0201
        return falcon_event.cloud_provider == 'AWS_EC2'

    def process(self, falcon_event):  # pylint: disable=R0201
        Submitter(falcon_event).submit()


__all__ = ['Runtime']
