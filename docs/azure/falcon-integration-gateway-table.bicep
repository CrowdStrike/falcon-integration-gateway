// Module: FalconIntegrationGatewayLogs_CL table
//
// Called by falcon-integration-gateway-dcr.bicep with a cross-scope module reference
// when the Log Analytics workspace is in a different resource group or subscription
// than the DCR deployment target.

@description('Name of the existing Log Analytics workspace.')
param workspaceName string

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  name: workspaceName
}

resource table 'Microsoft.OperationalInsights/workspaces/tables@2022-10-01' = {
  parent: workspace
  name: 'FalconIntegrationGatewayLogs_CL'
  properties: {
    schema: {
      name: 'FalconIntegrationGatewayLogs_CL'
      columns: [
        {
          name: 'TimeGenerated'
          type: 'dateTime'
          description: 'Timestamp when the record was ingested.'
        }
        {
          name: 'ExternalUri'
          type: 'string'
          description: 'Direct link to the detection in the Falcon console.'
        }
        {
          name: 'FalconEventId'
          type: 'string'
          description: 'Unique identifier for the Falcon detection event.'
        }
        {
          name: 'ComputerName'
          type: 'string'
          description: 'Hostname of the affected endpoint.'
        }
        {
          name: 'Description'
          type: 'string'
          description: 'Human-readable description of the detection.'
        }
        {
          name: 'Severity'
          type: 'string'
          description: 'Severity name of the detection (Critical, High, Medium, Low, or Informational).'
        }
        {
          name: 'Title'
          type: 'string'
          description: 'Alert title including the affected instance identifier.'
        }
        {
          name: 'ProcessName'
          type: 'string'
          description: 'Name of the process that triggered the detection.'
        }
        {
          name: 'ProcessPath'
          type: 'string'
          description: 'File system path of the triggering process.'
        }
        {
          name: 'CommandLine'
          type: 'string'
          description: 'Full command line used to launch the triggering process.'
        }
        {
          name: 'DetectName'
          type: 'string'
          description: 'CrowdStrike detection rule name.'
        }
        {
          name: 'AccountId'
          type: 'string'
          description: 'Cloud provider account or subscription ID of the affected resource.'
        }
        {
          name: 'InstanceId'
          type: 'string'
          description: 'Cloud provider instance ID of the affected resource.'
        }
        {
          name: 'CloudProvider'
          type: 'string'
          description: 'Cloud provider reported by the Falcon sensor (AWS, Azure, GCP, or Unrecognized).'
        }
        {
          name: 'ResourceGroup'
          type: 'string'
          description: 'Resource group or zone group of the affected resource.'
        }
        {
          name: 'arc'
          type: 'dynamic'
          description: 'Azure Arc metadata (resourceName, resourceGroup, subscriptionId, tenantId, vmId). Present only when arc_autodiscovery is enabled in FIG config.'
        }
      ]
    }
  }
}
