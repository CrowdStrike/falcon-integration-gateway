# pylint: disable=broad-except
"""AWS Security Hub backend using OCSF 1.6 schema.

This backend sends CrowdStrike Falcon detection events to AWS Security Hub+
using the OCSF 1.6 Detection Finding format and BatchImportFindingsV2 API.
"""

import logging
import boto3
from botocore.exceptions import ClientError
from ...config import config
from ...log import log
from .ocsf import OCSFDetectionFinding


class Submitter():
    def __init__(self, falcon_event):
        self.event = falcon_event
        self.region = config.get('aws_security_hub', 'region')
        self.endpoint_url = config.get('aws_security_hub', 'endpoint_url')

    def _get_client(self):
        """Create boto3 Security Hub client with optional endpoint URL."""
        kwargs = {'region_name': self.region}
        if self.endpoint_url:
            kwargs['endpoint_url'] = self.endpoint_url
        return boto3.client('securityhub', **kwargs)

    def _finding_exists(self, client, finding_uid):
        """Check if finding already exists in Security Hub+.

        Uses GetFindingsV2 filtering on finding_info.uid to deduplicate,
        mirroring the existing AWS backend's pattern.

        Args:
            client: boto3 Security Hub client
            finding_uid: The finding_info.uid value (event_id)

        Returns:
            True if finding exists, False otherwise
        """
        if not finding_uid:
            return False

        try:
            response = client.get_findings_v2(
                Filters=[
                    {
                        "StringFilters": [
                            {
                                "Name": "finding_info.uid",
                                "Value": finding_uid,
                                "Comparison": "EQUALS"
                            }
                        ]
                    }
                ],
                MaxResults=1
            )
            return len(response.get('Findings', [])) > 0
        except ClientError:
            pass
        return False

    def submit(self):
        log.info(
            "Processing detection for SecurityHub+ submission: %s (Offset: %s)",
            self.event.detect_description,
            self.event.original_event.offset
        )

        finding = OCSFDetectionFinding(self.event).build()
        finding_uid = finding.get('finding_info', {}).get('uid', '')

        try:
            client = self._get_client()

            # Deduplication check
            if self._finding_exists(client, finding_uid):
                if log.level <= logging.DEBUG:
                    log.debug(
                        "Detection already submitted to Security Hub+. "
                        "Alert not processed. (Offset: %s). "
                        "Finding UID: %s",
                        self.event.original_event.offset,
                        finding_uid
                    )
                else:
                    log.info(
                        "Detection already submitted to Security Hub+. "
                        "Alert not processed. (Offset: %s)",
                        self.event.original_event.offset
                    )
                return

            response = client.batch_import_findings_v2(
                Findings=[finding]
            )

            failed_count = response.get('FailedCount', 0)
            if failed_count > 0:
                failed_findings = response.get('FailedFindings', [])
                log.error(
                    "Failed to import %d finding(s): %s",
                    failed_count, failed_findings
                )
            else:
                try:
                    request_id = response.get(
                        'ResponseMetadata', {}
                    ).get('RequestId', 'UNKNOWN')
                    if log.level <= logging.DEBUG:
                        log.debug(
                            "Detection submitted to Security Hub+. "
                            "(Request ID: %s, Offset: %s). "
                            "Finding UID: %s",
                            request_id,
                            self.event.original_event.offset,
                            finding_uid
                        )
                    else:
                        log.info(
                            "Detection submitted to Security Hub+. "
                            "(Request ID: %s, Offset: %s)",
                            request_id,
                            self.event.original_event.offset
                        )
                except Exception as exc:
                    log.error(
                        "Error accessing response metadata: %s",
                        str(exc)
                    )

        except ClientError as err:
            log.exception(
                "Error submitting OCSF finding to Security Hub+: %s",
                str(err)
            )


class Runtime():
    RELEVANT_EVENT_TYPES = ['EppDetectionSummaryEvent']

    def __init__(self):
        log.info("AWS Security Hub+ (OCSF) Backend is enabled.")
        self.accept_all_events = config.getboolean(
            'aws_security_hub', 'accept_all_events'
        )

    def is_relevant(self, falcon_event):
        return (
            self.accept_all_events
            or (falcon_event.cloud_provider is not None
                and falcon_event.cloud_provider[:3].upper() == 'AWS')
        )

    def process(self, falcon_event):
        Submitter(falcon_event).submit()


__all__ = ['Runtime']
