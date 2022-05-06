from datetime import datetime
import ipaddress
from urllib.parse import quote
from json import dumps
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
from ...log import log
from ...config import config

SCOPES = ['https://www.googleapis.com/auth/malachite-ingestion']


def parse_url(url):
    try:
        cid = url.split("_")[-1]
        segments = url.split("/")
        relevant_url = ""
        for i in range(3, len(segments)):
            relevant_url += "/" + segments[i]
        parsed_relevant_url = quote(relevant_url, safe='')
        final_url = segments[0] + "/"
        final_url += segments[1] + "/"
        final_url += segments[2] + "/api2/link?"
        final_url += cid + "&url=" + parsed_relevant_url
        return final_url.split("_")[0]
    except IndexError as error:
        log.error("Failed to parse FalconHostLink: %s", error)
        return None


# Computes the size of a string in bytes
def utf8len(my_string):
    return len(my_string.encode('utf-8'))


class Submitter():
    def __init__(self):
        self.region = config.get('chronicle', 'region')
        self.customer_id = config.get('chronicle', 'customer_id')
        self.http_client = self.build_http_client()
        self.event = None

    def submit(self, event):
        self.event = event
        log.info("Processing detection: %s", self.event.original_event['event']['DetectId'])
        self.post_to_chronicle(self.udm(), self.region, self.customer_id)

    # Maps detection events into UDM
    def udm(self):
        event = self.event.original_event['event']
        meta = self.event.original_event['metadata']
        timestamp_components = str(datetime.fromtimestamp(event["ProcessStartTime"])).split()
        new_url = parse_url(event["FalconHostLink"])
        udm_result = {
            "metadata": {
                "event_timestamp": timestamp_components[0] + "T" + timestamp_components[1] + "+00:00",
                "event_type": "PROCESS_UNCATEGORIZED",
                "description": event["DetectDescription"],
                "product_event_type": meta["eventType"],
                "product_log_id": event["DetectId"],
                "product_name": "Falcon",
                "vendor_name": "CrowdStrike"
            },
            "principal": {
                "asset_id": "CrowdStrike.Falcon:" + event["SensorId"],
                "hostname": event["ComputerName"],
                "user": {
                    "userid": event["UserName"]
                },
                "ip": self.check_ip(event["LocalIP"])
            },
            "target": {
                "process": {
                    "command_line": event["CommandLine"],
                    "file": {
                        "full_path": event["FilePath"] + "\\" + event["FileName"],
                        "md5": event["MD5String"],
                        "sha1": event["SHA1String"],
                        "sha256": event["SHA256String"]
                    },
                    "pid": str(event["ProcessId"]),
                    "parent_process": {
                        "command_line": event["ParentCommandLine"],
                        "pid": str(event["ParentProcessId"])
                    }
                }
            },
            "security_result": {
                "action_details": event["PatternDispositionDescription"],
                "severity_details": event["SeverityName"],
                "url_back_to_product": new_url
            }
        }
        return udm_result

    @staticmethod
    def check_ip(data):
        try:
            ipaddress.ip_address(data)
            return data
        except ValueError:
            return "127.0.0.1"

    # Posts detection to Chronicle
    def post_to_chronicle(self, detection, region, customer_id):
        # Only Chronicle's US region doesn't have an API prefix
        prefix = region + '-'
        if region == 'us':
            prefix = ''
        # Set up the url and header
        url = "https://" + prefix + "malachiteingestion-pa.googleapis.com/v2/udmevents:batchCreate"
        headers = {'Content-Type': 'application/json'}
        # Format the events field
        payload = {"customer_id": customer_id, "events": [detection]}
        # Post to Chronicle
        response = self.http_client.post(url, data=dumps(payload), headers=headers)
        # Log any errors
        if response.status_code < 200 or response.status_code > 299:
            log.error("Error posting %s to Chronicle: %s", detection['metadata']['product_log_id'], response.text)
            log.error("Faulty detection: %s", dumps(payload, indent=4, sort_keys=True))
        else:
            log.info("Successfully posted %s to Chronicle:\t Byte count: %s", detection['metadata']['product_log_id'], utf8len(dumps(payload)))

    @staticmethod
    def build_http_client():
        service_account_file = config.get('chronicle', 'service_account')
        # get google token
        credentials = service_account.Credentials.from_service_account_file(service_account_file, scopes=SCOPES)
        # Build an HTTP client to make authorized OAuth requests.
        return AuthorizedSession(credentials)


class Runtime():
    def __init__(self):
        log.info("Chronicle backend is enabled.")
        self.submitter = Submitter()

    def is_relevant(self, falcon_event):  # pylint: disable=R0201,W0613
        return True

    def process(self, falcon_event):  # pylint: disable=R0201
        self.submitter.submit(falcon_event)


__all__ = ['Runtime']
