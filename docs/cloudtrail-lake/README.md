# Falcon Integration Gateway for AWS CloudTrail Lake - Deployment Guide
This guide presents the different Deployment strategies that can be utilized to deploy the Falcon
Integration Gateway to send events to AWS CloudTrail Lake. Only the CloudTrail Lake
[backend](https://github.com/CrowdStrike/falcon-integration-gateway/tree/main/fig/backends) will be enabled
by this guide.

## Prerequisites
- #### Have a current CrowdStrike Subscription

- #### CrowdStrike API Key Pair

    This key pair will be used to read falcon events and supplementary information from CrowdStrike Falcon.
    > If you need to create a new API key pair, review our docs: [CrowdStrike Falcon](https://falcon.crowdstrike.com/support/api-clients-and-keys).

    Make sure only the following permissions are assigned to the key pair:
    * Event streams: READ
    * Hosts: READ
- #### Values
    Regardless of which deployment method you choose, the following values should be known ahead of time:

    - Falcon API Credentials:
        - Falcon Client ID
        - Falcon Client Secret
        - Falcon Client Region
    - CloudTrail Lake:
        - Channel ARN (from [Getting Started](https://github.com/CrowdStrike/Cloud-AWS/tree/main/cloudtrail-lake#getting-started) guide)
        - AWS Region associated with Channel

## Deployment Strategies
Following our [Deployment](https://github.com/CrowdStrike/falcon-integration-gateway#deployment)
strategies for the FIG, and depending on your situation, the following strategies are available for this backend:

### [Deployment to EKS](./eks)
> Deploy FIG on EKS with Helm chart or Kube spec
### [Manual Deployment](./manual)
> Deploy FIG via Docker
