# Azure Backend

Integration with Microsoft Azure Log Analytics using the [Logs Ingestion API](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/logs-ingestion-api-overview).

> **Note:** The previous HTTP Data Collector API (SharedKey / `workspace_id` + `primary_key`) is deprecated by Microsoft. See the [Legacy mode](#legacy-mode-deprecated) section for backward-compatibility details.

---

## Authentication Modes

Set `auth_method` in the `[azure]` section of your config (or via `AZURE_AUTH_METHOD` env var):

| Value | Description |
|---|---|
| `workload_identity` | Azure Workload Federated Identity via `DefaultAzureCredential` — recommended for AKS |
| `client_secret` | Entra App Registration with a client secret — suitable for dev/test |
| `legacy` | Deprecated HTTP Data Collector API using SharedKey — backward compat only |

---

## Azure Setup (Required for `workload_identity` and `client_secret` modes)

Perform these steps once per target Log Analytics workspace in **Tenant B**.

### 1. Create a Microsoft Entra App Registration in Tenant B

Create an App Registration (SPN) in the target tenant. Note the **Application (client) ID** and **Directory (tenant) ID**.

### 2–4. Deploy the Custom Table, DCR, and Role Assignment (Bicep)

Steps 2, 3, and 4 (custom table, DCR, and role assignment) are automated by the provided Bicep template at [docs/azure/falcon-integration-gateway-dcr.bicep](../../docs/azure/falcon-integration-gateway-dcr.bicep).

```bash
# Retrieve the SPN object ID (run in Tenant B)
az ad sp show --id <application-client-id> --query id -o tsv

# Deploy the table, DCR, and role assignment
az deployment group create \
  --resource-group <resource-group-containing-log-analytics-workspace> \
  --template-file docs/azure/falcon-integration-gateway-dcr.bicep \
  --parameters \
      workspaceResourceId="<full-resource-id-of-log-analytics-workspace>" \
      monitoringMetricsPublisherPrincipalId="<spn-object-id>"
```

The deployment outputs `dcrEndpoint` and `dcrImmutableId` — use these as `azure.dcr_endpoint` and `azure.dcr_immutable_id` in your FIG configuration.

If you prefer to create these resources manually, the Bicep file documents the required table schema and DCR configuration.

> **Note:** The role assignment in the Bicep is scoped to the DCR resource only, following least-privilege. The SPN is granted permission to publish data to this DCR and nothing else.

---

## Workload Federated Identity Setup (AKS)

Use this mode when FIG runs on AKS and needs to publish to a Log Analytics workspace in a **different tenant**.

### One-time AKS cluster setup (Tenant A)

```bash
az aks update \
  --enable-oidc-issuer \
  --enable-workload-identity \
  --name <cluster-name> \
  --resource-group <resource-group>
```

Retrieve the cluster's OIDC issuer URL — you will need it in the next step:

```bash
az aks show \
  --name <cluster-name> \
  --resource-group <resource-group> \
  --query "oidcIssuerProfile.issuerUrl" -o tsv
```

### Configure federated identity credential on the SPN (Tenant B)

On the App Registration created in Azure Setup step 1, add a **Federated credential**:

| Field | Value |
|---|---|
| **Issuer** | The OIDC issuer URL from the cluster (retrieved above) |
| **Subject** | `system:serviceaccount:<namespace>:<k8s-service-account-name>` |
| **Audience** | `api://AzureADTokenExchange` |

> The subject must exactly match the Kubernetes namespace and ServiceAccount name used in your deployment. For multiple FIG instances targeting different workspaces, each needs its own ServiceAccount and its own federated credential on the corresponding SPN.

### Deploy

Use the updated [docs/aks/falcon-integration-gateway.yaml](../../docs/aks/falcon-integration-gateway.yaml), replacing all `REPLACE_ME_*` placeholders. The manifest creates the ServiceAccount, Secret, ConfigMap, and Deployment in a single `kubectl apply`.

The Azure Workload Identity webhook automatically injects `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, and `AZURE_FEDERATED_TOKEN_FILE` into the pod — no secrets for Azure credentials are stored in Kubernetes.

### Example `[azure]` config for `workload_identity` mode

```ini
[azure]
auth_method = workload_identity
dcr_endpoint = https://<dcr-endpoint>.ingest.monitor.azure.com
dcr_immutable_id = dcr-00000000000000000000000000000000
arc_autodiscovery = false
```

---

## Client Secret Mode

Suitable for non-AKS deployments or development environments.

### Example `[azure]` config

```ini
[azure]
auth_method = client_secret
tenant_id = <tenant-b-id>
client_id = <spn-client-id>
client_secret = <spn-client-secret>
dcr_endpoint = https://<dcr-endpoint>.ingest.monitor.azure.com
dcr_immutable_id = dcr-00000000000000000000000000000000
arc_autodiscovery = false
```

### Environment variables

| Variable | Config key |
|---|---|
| `AZURE_AUTH_METHOD` | `azure.auth_method` |
| `AZURE_TENANT_ID` | `azure.tenant_id` |
| `AZURE_CLIENT_ID` | `azure.client_id` |
| `AZURE_CLIENT_SECRET` | `azure.client_secret` |
| `AZURE_DCR_ENDPOINT` | `azure.dcr_endpoint` |
| `AZURE_DCR_IMMUTABLE_ID` | `azure.dcr_immutable_id` |

### Docker run example

```bash
docker run -it --rm \
  -e FALCON_CLIENT_ID="$FALCON_CLIENT_ID" \
  -e FALCON_CLIENT_SECRET="$FALCON_CLIENT_SECRET" \
  -e AZURE_AUTH_METHOD="client_secret" \
  -e AZURE_TENANT_ID="$AZURE_TENANT_ID" \
  -e AZURE_CLIENT_ID="$AZURE_CLIENT_ID" \
  -e AZURE_CLIENT_SECRET="$AZURE_CLIENT_SECRET" \
  -e AZURE_DCR_ENDPOINT="$AZURE_DCR_ENDPOINT" \
  -e AZURE_DCR_IMMUTABLE_ID="$AZURE_DCR_IMMUTABLE_ID" \
  -e FALCON_CLOUD_REGION="us-1" \
  falcon-integration-gateway:latest
```

---

## Legacy Mode (Deprecated)

> **Warning:** The HTTP Data Collector API used by legacy mode is deprecated by Microsoft and will be retired. Migrate to `workload_identity` or `client_secret` mode.

Legacy mode is used automatically when `auth_method = legacy` (the default if not set). A deprecation warning is logged at startup.

```ini
[azure]
auth_method = legacy
workspace_id = <log-analytics-workspace-id>
primary_key = <log-analytics-primary-key>
arc_autodiscovery = false
```

---

## API Scopes

Configure the following additional API scopes in your CrowdStrike Falcon console:

- **Real Time Response**: [Read, Write]
  > *Required only if using the Azure Arc Autodiscovery feature (`arc_autodiscovery = true`).*

---

## Developer Resources

- [Logs Ingestion API overview](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/logs-ingestion-api-overview)
- [Tutorial: Send data to Azure Monitor using Logs ingestion API](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/tutorial-logs-ingestion-api)
- [Azure Workload Identity for AKS](https://azure.github.io/azure-workload-identity/docs/)
- [Migrate from HTTP Data Collector API](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/custom-logs-migrate)

