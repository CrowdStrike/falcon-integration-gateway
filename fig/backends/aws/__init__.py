# pylint: disable=broad-except
from datetime import datetime, timezone
import logging
import traceback
import boto3
from botocore.exceptions import ClientError
from ...config import config
from ...log import log
from ... import __version__


class Submitter():
    def __init__(self, event):
        self.event = event
        self.region = config.get('aws', 'region')
        self.confirm_instance = config.getboolean('aws', 'confirm_instance')
        self.accept_all_events = config.getboolean('aws', 'accept_all_events')

    def _is_aws_event(self):
        """Check if the event originates from AWS cloud provider."""
        return (self.event.cloud_provider is not None and
                self.event.cloud_provider[:3].upper() == 'AWS')

    def _should_skip_instance_confirmation(self):
        """Determine if AWS instance confirmation should be bypassed for non-AWS events."""
        return self.accept_all_events and not self._is_aws_event()

    def _build_enhanced_resource_details(self):
        """Build enhanced resource details using CrowdStrike device data."""
        details = {}

        # Device details field mapping
        device_field_mapping = {
            'hostname': 'Hostname',
            'device_id': 'AID',
            'platform_name': 'Platform',
            'external_ip': 'ExternalIP',
            'local_ip': 'LocalIP',
            'mac_address': 'MACAddress',
            'domain': 'Domain',
            'agent_version': 'AgentVersion',
            'last_seen_timestamp': 'LastSeenTimestamp',
            'os_version': 'OSVersion',
            'device_tags': 'DeviceTags',
            'site_name': 'SiteName',
            'organizational_unit': 'OrganizationalUnit'
        }

        # Extract device details using comprehension
        device_details = getattr(self.event, 'device_details', {}) or {}
        details.update({
            output_key: device_details[input_key]
            for input_key, output_key in device_field_mapping.items()
            if device_details.get(input_key)
        })

        # Cloud context field mapping
        cloud_field_mapping = {
            'cloud_provider': 'CloudProvider',
            'cloud_provider_account_id': 'CloudAccountId',
            'instance_id': 'InstanceId'
        }

        # Extract cloud context using comprehension
        details.update({
            output_key: getattr(self.event, input_key)
            for input_key, output_key in cloud_field_mapping.items()
            if getattr(self.event, input_key, None)
        })

        return details

    def _determine_resource_info(self):
        """Determine appropriate resource type and ID."""
        is_aws = self._is_aws_event()

        if is_aws:
            # AWS events use existing AwsEc2Instance type
            resource_type = "AwsEc2Instance"
            resource_id = self.event.instance_id or f"UnknownInstanceId:{self.event.event_id}"
            title_suffix = f"Instance: {resource_id}"
            resource_details = None  # AWS events use existing logic
        else:
            # Non-AWS events use Other type with sensor_id as resource_id
            resource_type = "Other"
            resource_id = self.event.original_event.sensor_id
            title_suffix = self._build_title_suffix(resource_id)
            resource_details = self._build_enhanced_resource_details()

        return resource_type, resource_id, title_suffix, resource_details

    def _build_title_suffix(self, resource_id):
        """Build descriptive title suffix for non-AWS events."""
        cloud_provider = getattr(self.event, 'cloud_provider', None)
        if cloud_provider:
            return f"{cloud_provider} Host: {resource_id}"
        return f"Host: {resource_id}"

    def find_instance(self, instance_id, mac_address):
        # Instance IDs are unique to the region, not the account, so we have to check them all
        report_region = self.region
        ec2instance = None
        ec2_client = boto3.client("ec2", region_name=report_region)
        regions = [region["RegionName"] for region in ec2_client.describe_regions()["Regions"]]
        for region in regions:
            ec2 = boto3.resource("ec2", region_name=region)
            try:
                ec2instance = ec2.Instance(instance_id)
                found = False
                # Confirm the mac address matches
                if ec2instance.network_interfaces:
                    for iface in ec2instance.network_interfaces:
                        det_mac = mac_address.lower().replace(":", "").replace("-", "")
                        ins_mac = iface.mac_address.lower().replace(":", "").replace("-", "")
                        if det_mac == ins_mac:
                            found = True
                if found:  # pylint: disable=R1723
                    return region, ec2instance
            except ClientError:
                continue
            except Exception:  # pylint: disable=W0703
                trace = traceback.format_exc()
                log.exception(str(trace))
                continue

        return report_region, ec2instance

    @staticmethod
    def send_to_securityhub(manifest, region):
        client = boto3.client('securityhub', region_name=region)
        check_response = {}
        found = False
        try:
            check_response = client.get_findings(Filters={'Id': [{'Value': manifest["Id"], 'Comparison': 'EQUALS'}]})
            for _ in check_response["Findings"]:
                found = True
        except ClientError:
            pass

        import_response = False
        if not found:
            try:
                import_response = client.batch_import_findings(Findings=[manifest])
            except ClientError as err:
                # Boto3 issue communicating with SH, throw the error in the log
                log.exception(str(err))

        return import_response

    def submit(self):
        log.info("Processing detection: %s (Offset: %s)", self.event.detect_description, self.event.original_event.offset)
        det_region = self.region
        send = False

        if self._should_skip_instance_confirmation():
            # For non-AWS events when accept_all_events is True, skip AWS instance confirmation
            send = True
            log.debug("Skipping AWS instance confirmation for non-AWS event (accept_all_events=True)")
        elif self.confirm_instance:
            try:
                if self.event.instance_id:
                    det_region, instance = self.find_instance(self.event.instance_id, self.event.device_details["mac_address"])
                    if instance is None:
                        log.warning("Instance %s with MAC address %s not found in regions searched. Alert not processed.",
                                    self.event.instance_id, self.event.device_details["mac_address"])
                        return
                    try:
                        if instance.network_interfaces:
                            for _ in instance.network_interfaces:
                                # Only send alerts for instances we can find
                                send = True

                    except ClientError:
                        # Not our instance
                        i_id = self.event.instance_id
                        mac = self.event.device_details["mac_address"]
                        log.info("Instance %s with MAC address %s not found in regions searched. Alert not processed.", i_id, mac)
            except AttributeError:
                # Instance ID was not provided by the detection
                log.info("Instance ID not provided by detection. Alert not processed.")
        else:
            # If we're not confirming the instance, we can just send the alert
            send = True

        if send:
            sh_payload = self.create_payload(det_region)
            response = self.send_to_securityhub(sh_payload, det_region)
            if not response:
                if log.level <= logging.DEBUG:
                    log.debug("Detection already submitted to Security Hub. Alert not processed. (Offset: %s). Payload info: %s", self.event.original_event.offset, sh_payload)
                else:
                    log.info("Detection already submitted to Security Hub. Alert not processed. (Offset: %s)", self.event.original_event.offset)
            else:
                try:
                    success_count = response.get("SuccessCount", 0)

                    if success_count > 0:
                        try:
                            request_id = response.get('ResponseMetadata', {}).get('RequestId', 'UNKNOWN')
                            if log.level <= logging.DEBUG:
                                log.debug("Detection submitted to Security Hub. (Request ID: %s, Offset: %s). Payload info: %s",
                                          request_id, self.event.original_event.offset, sh_payload)
                            else:
                                log.info("Detection submitted to Security Hub. (Request ID: %s, Offset: %s)", request_id, self.event.original_event.offset)
                        except Exception as e:
                            log.error("Error accessing response metadata: %s", str(e))
                            log.info("Detection submitted to Security Hub (Request ID unavailable due to error, Offset: %s)", self.event.original_event.offset)
                    else:
                        log.warning("SuccessCount is 0 or missing - submission may have failed (Offset: %s)", self.event.original_event.offset)
                        log.debug("Full response for debugging (Offset: %s): %s", self.event.original_event.offset, response)
                except Exception as e:
                    log.error("Error processing Security Hub response: %s (Offset: %s)", str(e), self.event.original_event.offset)
                    log.exception("Response processing exception details:")
                    log.debug("Raw response that caused error (Offset: %s): %s", self.event.original_event.offset, response)

    def create_payload(self, instance_region):  # pylint: disable=too-many-locals
        region = self.region
        try:
            account_id = boto3.client("sts", region_name=region).get_caller_identity().get('Account')
        except KeyError:
            # Failed to get endpoint_resolver the first time, try it again
            account_id = boto3.client("sts", region_name=region).get_caller_identity().get('Account')
        severity_original = self.event.severity
        severity_label = severity_original.upper()
        if "gov" in region:
            ARN = "arn:aws-us-gov:securityhub:{}:358431324613:product/crowdstrike/crowdstrike-falcon".format(region)
        else:
            ARN = "arn:aws:securityhub:{}:517716713836:product/crowdstrike/crowdstrike-falcon".format(region)
        payload = {
            "SchemaVersion": "2018-10-08",
            "ProductArn": f"{ARN}",
            "AwsAccountId": account_id,
            "SourceUrl": self.event.falcon_link,
            "GeneratorId": "Falcon Host",
            "CreatedAt": datetime.fromtimestamp(float(self.event.event_create_time) / 1000., tz=timezone.utc).isoformat().replace('+00:00', 'Z'),
            "UpdatedAt": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "RecordState": "ACTIVE",
            "Severity": {"Label": severity_label, "Original": severity_original},
            "ProductFields": self.build_product_fields(),
        }

        # Instance ID based detail - use helper method for proper resource classification
        resource_type, resource_id, title_suffix, resource_details = self._determine_resource_info()
        payload["Id"] = f"crowdstrike:crowdstrike-falcon:{self.event.event_id}"
        payload["Title"] = f"Falcon Alert. {title_suffix}"

        # Build Resources section with enhanced details for non-AWS events
        resource_entry = {"Type": resource_type, "Id": resource_id, "Region": instance_region}
        if resource_details:
            # Add ResourceDetails using ASFF "Other" object for enhanced context
            resource_entry["Details"] = {"Other": resource_details}

        payload["Resources"] = [resource_entry]
        # Description
        cloud_account_info = ""
        if self.event.cloud_provider_account_id:
            cloud_provider = getattr(self.event, 'cloud_provider', 'Cloud')
            cloud_account_info = f"| {cloud_provider} Account: {self.event.cloud_provider_account_id}"
        payload["Description"] = f"{self.event.detect_description} {cloud_account_info}"

        # TTPs with simple fallback to MitreAttack
        try:
            tactic = self.event.original_event["event"]["Tactic"]
            technique = self.event.original_event["event"]["Technique"]
        except KeyError:
            # Fallback to first MitreAttack entry
            try:
                mitre_data = self.event.original_event["event"]["MitreAttack"]
                if mitre_data and len(mitre_data) > 0:
                    tactic = mitre_data[0].get("Tactic")
                    technique = mitre_data[0].get("Technique")
                else:
                    tactic = technique = None
            except (KeyError, IndexError, TypeError):
                tactic = technique = None

        if tactic and technique:
            payload["Types"] = ["Namespace: TTPs",
                                f"Category: {tactic}",
                                f"Classifier: {technique}"
                                ]

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

    def build_product_fields(self):
        """
        Build ProductFields with core fields for AWS Security Hub.

        Extracts important fields to add context to the detection. Please NOTE that there
        is a max limit of 50 properties per the ProductFields object.

        Returns:
            dict: ProductFields dictionary with crowdstrike/crowdstrike-falcon/ prefixed keys
        """

        # Initialize ProductFields with core information
        product_fields = {
            "crowdstrike/crowdstrike-falcon/cid": self.event.cid,
            "crowdstrike/crowdstrike-falcon/FigVersion": __version__
        }

        # Get event data safely
        try:
            event_data = self.event.original_event.get('event', {})
        except (AttributeError, TypeError) as e:
            log.warning("Failed to get event data: %s", str(e))
            return product_fields

        if not event_data:
            log.debug("No event data found, returning core ProductFields")
            return product_fields

        # Core fields for analysis.
        target_fields = [
            # File and Hash Information
            'FileName', 'FilePath', 'SHA256String', 'SHA1String', 'MD5String',
            # Process Context
            'CommandLine', 'ParentImageFileName', 'ParentCommandLine', 'GrandParentImageFileName', 'GrandParentCommandLine',
            # Indicator Context
            'IOCType', 'IOCValue', 'AssociatedFile', 'PatternDispositionDescription',
            # Behavioral Classification
            'Tactic', 'Technique', 'Objective'
        ]

        # Extract fields
        for field_name in target_fields:
            if field_name in event_data:
                try:
                    value = str(event_data[field_name])
                    product_fields[f"crowdstrike/crowdstrike-falcon/{field_name}"] = value
                except Exception as e:
                    log.warning("Error processing field %s: %s", field_name, str(e))

        # Handle MitreAttack array separately due to nested structure
        try:
            if 'MitreAttack' in event_data:
                mitre_data = event_data['MitreAttack']
                if isinstance(mitre_data, list) and mitre_data:
                    # Process up to 5 MITRE entries to stay within limits
                    for i, entry in enumerate(mitre_data[:5]):
                        if isinstance(entry, dict):
                            entry_prefix = f"crowdstrike/crowdstrike-falcon/MitreAttack/{i}"
                            # Add key MITRE fields
                            for key in ['Tactic', 'TacticID', 'Technique', 'TechniqueID', 'PatternID']:
                                if key in entry:
                                    try:
                                        value = str(entry[key])
                                        product_fields[f"{entry_prefix}/{key}"] = value
                                    except Exception as e:
                                        log.warning("Error processing MITRE field %s: %s", key, str(e))
        except Exception as e:
            log.warning("Error adding MitreAttack fields: %s", str(e))

        return product_fields

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
    RELEVANT_EVENT_TYPES = ['EppDetectionSummaryEvent']

    def __init__(self):
        log.info("AWS Backend is enabled.")
        self.accept_all_events = config.getboolean('aws', 'accept_all_events')

    def is_relevant(self, falcon_event):
        return self.accept_all_events or (falcon_event.cloud_provider is not None and falcon_event.cloud_provider[:3].upper() == 'AWS')

    def process(self, falcon_event):
        Submitter(falcon_event).submit()


__all__ = ['Runtime']
