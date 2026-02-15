"""OCSF 1.6 Detection Finding builder for CrowdStrike Falcon events."""

from datetime import datetime, timezone

# AWS-assigned product UID for CrowdStrike Falcon OCSF integration
PRODUCT_UID = "9ad39a27-ac7b-4087-aa0a-551cbec8d9c5"

# Severity mapping using SeverityName (string) not Severity (numeric)
SEVERITY_MAP = {
    "Critical": (5, "Critical"),
    "High": (4, "High"),
    "Medium": (3, "Medium"),
    "Low": (2, "Low"),
    "Informational": (1, "Informational"),
}


def map_severity(severity_name):
    """Map CrowdStrike SeverityName to OCSF severity_id and severity string.

    Args:
        severity_name: CrowdStrike severity name
            (Critical, High, Medium, Low, Informational)

    Returns:
        Tuple of (severity_id, severity_string)
    """
    return SEVERITY_MAP.get(severity_name, (0, "Unknown"))


class OCSFDetectionFinding:
    """Builds OCSF 1.6 Detection Finding from CrowdStrike Falcon event."""

    def __init__(self, falcon_event):
        """Initialize with a FalconEvent instance.

        Args:
            falcon_event: FalconEvent instance from fig.falcon_data
        """
        self.falcon_event = falcon_event
        self.event = falcon_event.original_event.get('event', {})
        self.event_metadata = falcon_event.original_event.get('metadata', {})

    def build(self):
        """Build complete OCSF 1.6 Detection Finding payload.

        Returns:
            Dict containing OCSF-compliant detection finding
        """
        severity_id, severity_name = map_severity(
            self.event.get('SeverityName', '')
        )

        return {
            # Static OCSF fields
            "class_uid": 2004,
            "class_name": "Detection Finding",
            "category_uid": 2,
            "category_name": "Findings",
            "activity_id": 1,
            "activity_name": "Create",
            "type_uid": 200401,
            "type_name": "Detection Finding: Create",

            # Timestamps
            "time": self._epoch_seconds_to_ms(
                self.event.get('ProcessStartTime')
            ),
            "metadata": self._build_metadata(),

            # Severity
            "severity_id": severity_id,
            "severity": severity_name,

            # Event details
            "message": self.event.get('Description', ''),
            "status": self.event.get(
                'PatternDispositionDescription', ''
            ),
            "status_detail": self.event.get(
                'PatternDispositionDescription', ''
            ),

            # Finding info
            "finding_info": self._build_finding_info(),

            # Resources (process)
            "resources": [self._build_process_resource()],

            # CrowdStrike extensions
            "unmapped": self._build_unmapped(),
        }

    def _epoch_seconds_to_ms(self, epoch_seconds):
        """Convert epoch seconds to milliseconds for OCSF timestamp."""
        if epoch_seconds:
            return int(epoch_seconds) * 1000
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    def _build_metadata(self):
        """Build OCSF metadata section."""
        return {
            "version": "1.6.0",
            "logged_time": self.event_metadata.get('eventCreationTime'),
            "product": {
                "name": self.event.get(
                    'SourceProducts', 'Falcon Insight'
                ),
                "vendor_name": self.event.get(
                    'SourceVendors', 'CrowdStrike'
                ),
                "uid": PRODUCT_UID,
            }
        }

    def _build_finding_info(self):
        """Build OCSF finding_info section with MITRE ATT&CK mapping."""
        finding = {
            "title": self.event.get('Name', ''),
            "uid": self.falcon_event.event_id,
        }

        attacks = self._build_attacks()
        if attacks:
            finding["attacks"] = attacks

        return finding

    def _build_attacks(self):
        """Build MITRE ATT&CK mapping from event data."""
        attacks = []
        mitre_data = self.event.get('MitreAttack', [])

        if mitre_data:
            for entry in mitre_data:
                attack = {
                    "tactic": {
                        "name": entry.get('Tactic', ''),
                        "uid": entry.get('TacticID', ''),
                    },
                    "technique": {
                        "name": entry.get('Technique', ''),
                        "uid": entry.get('TechniqueID', ''),
                    }
                }
                attacks.append(attack)

        # Fallback to top-level Tactic/Technique if no MitreAttack array
        if not attacks and self.event.get('Tactic'):
            attacks.append({
                "tactic": {"name": self.event.get('Tactic', '')},
                "technique": {"name": self.event.get('Technique', '')},
            })

        return attacks

    def _build_process_resource(self):
        """Build OCSF resources section for process information."""
        return {
            "uid": str(self.event.get('ProcessId', '')),
            "name": self.event.get('FileName', ''),
            "hostname": self.event.get('Hostname', ''),
            "ip": self.event.get('LocalIP', ''),
            "type": "Process",
            "data": {
                "cmd_line": self.event.get('CommandLine', ''),
                "file_path": self.event.get('FilePath', ''),
                "sha256": self.event.get('SHA256String', ''),
                "md5": self.event.get('MD5String', ''),
                "user_name": self.event.get('UserName', ''),
                "parent_pid": str(
                    self.event.get('ParentProcessId', '')
                ),
                "parent_cmd_line": self.event.get(
                    'ParentCommandLine', ''
                ),
            }
        }

    def _build_unmapped(self):
        """Build CrowdStrike-specific extension fields."""
        return {
            "agent_id": self.event.get('AgentId', ''),
            "composite_id": self.event.get('CompositeId', ''),
            "hostname": self.event.get('Hostname', ''),
            "local_ip": self.event.get('LocalIP', ''),
            "mac_address": self.event.get('MACAddress', ''),
            "platform_name": self.event.get('PlatformName', ''),
            "container_id": self.event.get('ContainerId', ''),
            "falcon_link": self.event.get('FalconHostLink', ''),
            "risk_score": self.event.get('RiskScore'),
            "grandparent_file_name": self.event.get(
                'GrandParentImageFileName', ''
            ),
            "grandparent_cmd_line": self.event.get(
                'GrandParentCommandLine', ''
            ),
        }
