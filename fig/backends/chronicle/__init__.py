from datetime import datetime
from urllib.parse import quote
from json import dumps
from requests import request
from ...log import log
from ...config import config


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


class Submitter():
    def __init__(self, event):
        self.event = event
        self.security_key = config.get('chronicle', 'security_key')
        self.region = config.get('chronicle', 'region')

    def submit(self):
        log.info("Processing detection: %s", self.event.detect_description)
        self.post_to_chronicle(self.udm())

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
                "product_name": "Falcon"
            },
            "principal": {
                "hostname": event["ComputerName"],
                "user": {
                    "userid": event["UserName"]
                },
                "ip": event["LocalIP"]
            },
            "target": {
                "asset_id": "CrowdStrike.Falcon:" + event["SensorId"],
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

    def post_to_chronicle(self, event):
        # Only Chronicle's US region doesn't have an API prefix
        prefix = self.region
        if self.region == 'us':
            prefix = ''

        url = "https://" + prefix + "malachiteingestion-pa.googleapis.com/v1/udmevents?key=" + self.security_key
        headers = {'Content-Type': 'application/json'}
        payload = {"events": [event]}

        response = request("POST", url, data=dumps(payload), headers=headers)
        if response.status_code >= 400:
            log.error("Error logging to Chronicle: %s", response.text)


class Runtime():
    def __init__(self):
        log.info("Chronicle backend is enabled.")

    def is_relevant(self, falcon_event):  # pylint: disable=R0201,W0613
        return True

    def process(self, falcon_event):  # pylint: disable=R0201
        Submitter(falcon_event).submit()


__all__ = ['Runtime']
