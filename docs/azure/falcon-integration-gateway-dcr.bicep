// Falcon Integration Gateway — Azure Monitor Infrastructure
//
// Deploys the following resources in the target tenant (Tenant B):
//   - Custom Log Analytics table: FalconIntegrationGatewayLogs_CL
//   - Data Collection Rule (DCR): routes data from the Logs Ingestion API to the table
//   - Role assignment: grants the SPN Monitoring Metrics Publisher on the DCR (least privilege)
//
// The outputs (dcrEndpoint and dcrImmutableId) are the values required for the
// azure.dcr_endpoint and azure.dcr_immutable_id settings in the FIG configuration.
//
// Usage:
//   az deployment group create \
//     --resource-group <resource-group-containing-log-analytics-workspace> \
//     --template-file falcon-integration-gateway-dcr.bicep \
//     --parameters \
//         workspaceResourceId="<full-resource-id-of-log-analytics-workspace>" \
//         monitoringMetricsPublisherPrincipalId="<object-id-of-spn-in-this-tenant>"
//
// Retrieve the SPN object ID (run in Tenant B):
//   az ad sp show --id <application-client-id> --query id -o tsv

@description('Azure region where the DCR will be deployed. Must match the Log Analytics workspace region.')
param location string = resourceGroup().location

@description('Full resource ID of the existing Log Analytics workspace.')
param workspaceResourceId string

@description('Name of the Data Collection Rule.')
param dataCollectionRuleName string = 'dcr-falcon-integration-gateway'

@description('Object ID of the Service Principal (SPN) that will publish data to this DCR. Used to assign the Monitoring Metrics Publisher role scoped to this DCR.')
param monitoringMetricsPublisherPrincipalId string

// Parse workspace name, subscription, and resource group from the resource ID.
// The workspace may be in a different resource group or subscription within the same tenant.
var workspaceName = last(split(workspaceResourceId, '/'))
var workspaceSubscriptionId = split(workspaceResourceId, '/')[2]
var workspaceResourceGroupName = split(workspaceResourceId, '/')[4]

// Deploy the custom Log Analytics table via a module scoped to the workspace's resource group.
// Using a module is required because the table must be deployed to the workspace's scope,
// which may differ from the scope of this deployment (where the DCR lives).
module tableDeployment 'falcon-integration-gateway-table.bicep' = {
  name: 'falcon-integration-gateway-table'
  scope: resourceGroup(workspaceSubscriptionId, workspaceResourceGroupName)
  params: {
    workspaceName: workspaceName
  }
}

// Data Collection Rule — receives data via the Logs Ingestion API and routes it to the table above.
// kind: 'Direct' enables the DCR-level logsIngestion endpoint, avoiding the need for a separate DCE.
resource dcr 'Microsoft.Insights/dataCollectionRules@2023-03-11' = {
  name: dataCollectionRuleName
  location: location
  kind: 'Direct'
  properties: {
    streamDeclarations: {
      'Custom-FalconIntegrationGatewayLogs': {
        columns: [
          { name: 'TimeGenerated', type: 'datetime' }
          { name: 'ExternalUri', type: 'string' }
          { name: 'FalconEventId', type: 'string' }
          { name: 'ComputerName', type: 'string' }
          { name: 'Description', type: 'string' }
          { name: 'Severity', type: 'string' }
          { name: 'Title', type: 'string' }
          { name: 'ProcessName', type: 'string' }
          { name: 'ProcessPath', type: 'string' }
          { name: 'CommandLine', type: 'string' }
          { name: 'DetectName', type: 'string' }
          { name: 'AccountId', type: 'string' }
          { name: 'InstanceId', type: 'string' }
          { name: 'CloudProvider', type: 'string' }
          { name: 'ResourceGroup', type: 'string' }
          { name: 'arc', type: 'dynamic' }
        ]
      }
    }
    destinations: {
      logAnalytics: [
        {
          workspaceResourceId: workspaceResourceId
          name: 'destination-workspace'
        }
      ]
    }
    dataFlows: [
      {
        streams: [ 'Custom-FalconIntegrationGatewayLogs' ]
        destinations: [ 'destination-workspace' ]
        // Incoming data matches the table schema exactly — no transformation required
        transformKql: 'source'
        outputStream: 'Custom-FalconIntegrationGatewayLogs_CL'
      }
    ]
  }
  dependsOn: [
    tableDeployment
  ]
}

// Assign Monitoring Metrics Publisher to the SPN, scoped to this DCR only (least privilege).
// The SPN can publish data to this DCR but has no access to any other DCR or workspace resource.
var monitoringMetricsPublisherRoleId = '3913510d-42f4-4e42-8a64-420c390055eb'

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: dcr
  name: guid(dcr.id, monitoringMetricsPublisherPrincipalId, monitoringMetricsPublisherRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      monitoringMetricsPublisherRoleId
    )
    principalId: monitoringMetricsPublisherPrincipalId
    principalType: 'ServicePrincipal'
  }
}

@description('Logs ingestion endpoint URL. Use as azure.dcr_endpoint in the FIG configuration.')
// endpoints.logsIngestion is the DCR-level ingestion URL introduced with kind: Direct.
// any() is required because Bicep does not type-check sub-properties of the endpoints object.
output dcrEndpoint string = any(dcr.properties.endpoints).logsIngestion

@description('DCR immutable ID. Use as azure.dcr_immutable_id in the FIG configuration.')
output dcrImmutableId string = dcr.properties.immutableId

@description('Full resource ID of the Data Collection Rule.')
output dcrResourceId string = dcr.id
