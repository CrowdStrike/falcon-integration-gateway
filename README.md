# falcon-integration-gateway [![Python Lint](https://github.com/CrowdStrike/falcon-integration-gateway/actions/workflows/linting.yml/badge.svg)](https://github.com/CrowdStrike/falcon-integration-gateway/actions/workflows/linting.yml) [![Container Build on Quay](https://quay.io/repository/crowdstrike/falcon-integration-gateway/status "Docker Repository on Quay")](https://quay.io/repository/crowdstrike/falcon-integration-gateway)

Falcon Integration Gateway (FIG) forwards threat detection findings from CrowdStrike Falcon platform to the [backend](fig/backends) of your choice.

Learn more about CrowdStrike Falcon Threat Graph: [Product Page](https://www.crowdstrike.com/products/falcon-platform/threat-graph/), [Data Sheet](https://www.crowdstrike.com/resources/data-sheets/threat-graph/).

Currently available backends are
 * [AWS backend](fig/backends/aws) - pushes real-time threat detections to AWS Security Hub
 * [Azure backend](fig/backends/azure) - pushes real-time threat detections to Azure Log Analytics
 * [GCP Security Command Center](fig/backends/gcp) - pushes real-time threat detections to GCP Security Command Center

## Deployment Guide

- [Deployment to AKS](docs/aks)
- [Deployment to GKE](docs/gke)

## Developer Guide

Start with learning about the different [backends](fig/backends). Instructions may differ slightly depending on the backend of interest.
