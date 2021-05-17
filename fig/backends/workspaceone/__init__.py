from .serverlog import serverlog
from ...log import log
from ...config import config


class Submitter():
    def __init__(self, token, event):
        self.workspaceone_token = token
        self.event = event

    def submit(self):
        log.info("Processing detection: %s", self.event.detect_description)
        serverlog.info(self.log())

    def log(self):
        event = self.event.original_event['event']
        meta = self.event.original_event['metadata']
        msg = 'CEF:0|CrowdStrike|FalconHost|1.0|DetectionSummaryEvent|Detection Summary Event|2|'
        msg += 'Token=' + self.workspaceone_token
        msg += ' UDID=' + self.event.mdm_identifier
        if 'SensorId' in event:
            msg += ' externalId=' + event['SensorId']
        if 'ProcessId' in event:
            msg += ' cn2=' + str(event['ProcessId'])
            msg += ' cn2Label=ProcessId'
        if 'ParentProcessId' in event:
            msg += ' cn1=' + str(event['ParentProcessId'])
            msg += ' cn1Label=ParentProcessId'
        if 'UserName' in event:
            msg += ' suser=' + event['UserName']
        if 'DetectDescription' in event:
            msg += ' msg=' + event['DetectDescription']
        if 'FileName' in event:
            msg += ' fname=' + event['FileName']
        if 'FilePath' in event:
            msg += ' filePath=' + event['FilePath']
        if 'CommandLine' in event:
            msg += ' cs5=' + event['CommandLine']
            msg += ' cs5Label=CommandLine'
        if 'MD5String' in event:
            msg += ' fileHash=' + event['MD5String']
        if 'MachineDomain' in event:
            msg += ' sntdom=' + event['MachineDomain']
        if 'FalconHostLink' in event:
            msg += ' cs6=' + event['FalconHostLink']
            msg += ' cs6Label=FalconHostLink'
        if 'offset' in meta:
            msg += ' cn3=' + str(meta['offset'])
            msg += ' cn3Label=Offset'
        if 'eventCreationTime' in meta:
            msg += ' rt=' + str(meta['eventCreationTime'])
        if 'LocalIP' in event:
            msg += ' src=' + event['LocalIP']
        if 'MACAddress' in event:
            msg += ' smac=' + event['MACAddress']
        if 'Tactic' in event:
            msg += ' cat=' + event['Tactic']
        if 'Technique' in event:
            msg += ' act=' + event['Technique']
        if 'Objective' in event:
            msg += ' reason=' + event['Objective']
        if 'PatternDispositionValue' in event:
            msg += ' outcome=' + str(event['PatternDispositionValue'])
        if 'PatternDispositionDescription' in event:
            msg += ' CSMTRPatternDisposition=' + event['PatternDispositionDescription']
        return msg


class Runtime():
    def __init__(self):
        log.info("Workspace One backend is enabled.")
        self.workspaceone_token = config.get('workspaceone', 'token')

    def is_relevant(self, falcon_event):  # pylint: disable=R0201
        return falcon_event.mdm_identifier is not None

    def process(self, falcon_event):
        Submitter(self.workspaceone_token, falcon_event).submit()


__all__ = ['Runtime']
