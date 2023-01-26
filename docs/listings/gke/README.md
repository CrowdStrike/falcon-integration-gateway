# GKE Marketplace Listing

GKE marketplace listing consists of 4 parts:
 - application container
 - helm chart and the deployer metadata (in this directory)
 - deployer container (responsible for distributing and deploying the helm chart)
 - marketplace ui representation

Please consult GCP documentation to understand the topic of marketplace listings more broadly.

## Developer Links

 - GCP Documentation
   - [Requirement for packaging your app](https://cloud.google.com/marketplace/docs/partners/kubernetes/create-app-package)
   - [Deployer Schema](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/blob/master/docs/schema.md#x-google-marketplace-1)
   - [How to build deployer image: Step 1](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/blob/master/docs/building-deployer.md)
   - [How to build deployer image: Step 2](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/blob/master/docs/building-deployer-helm.md)
   - [How to install published marketplace application manually](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/blob/master/docs/mpdev-references.md#installing-a-published-marketplace-app)

## How to deploy manually?
```
mpdev install \
      --deployer=$REGISTRY/$APP_NAME/deployer \
      --parameters='{"name": "falcon-integration-gateway", "namespace": "test-ns", "falcon.cloud_region": "us-1", "falcon.client_id": "'${client_id}'", "falcon.client_secret": "'${client_secret}'", "cloud.google.application_credentials": "'$gcloud_creds'" }'
```

## How to run sanity test?
```
mpdev verify \
      --deployer=$REGISTRY/$APP_NAME/deployer
```

## How to update marketplace listing?

## Preparation

 - authenticate with GCP using gcloud
 - create your [GKE cluster](https://cloud.google.com/kubernetes-engine/docs/deploy-app-cluster#create_cluster) for testing, configure your kubectl command to use that cluster
 - install [mpdev](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/blob/master/docs/tool-prerequisites.md) command locally

## Push the application image

 - pull the FIG released application image from quay builder
 - push new version of the application image to `gcr.io/crowdstrike-public/falcon-integration-gateway-chronicle`
 - tag the pushed image with 3 tags, similar to following: `latest`, `3.1`, and `3.1.4`

## Build and Push the deployer image

 - refresh deployer base container locally
   ```
   docker pull gcr.io/cloud-marketplace-tools/k8s/deployer_helm/onbuild
   ```
 - build the image
    > Navigate to the `docs/listings/gke/deployer` directory before running the following commands
   ```
   IMAGE=gcr.io/crowdstrike-public/falcon-integration-gateway/deployer
   docker build --tag "$IMAGE:latest" .
   ```
 - push the image and tag it accordingly with 3 tags, similar to the following: `latest`, `3.1`, `3.1.4`

## Test the deployer and the application

 - Create namespace
   ```
   kubectl create namespace test-ns
   ```
 - Deploy the application
   ```
   FALCON_CLIENT_ID=
   FALCON_CLIENT_SECRET=
   GCLOUD_CREDS=$(base64 < "gcp_service_account_for_fig.json")
   mpdev install \
     --deployer=$IMAGE:latest \
     --parameters='{"name": "falcon-integration-gateway", "namespace": "test-ns", "falcon.cloud_region": "us-1", "falcon.client_id": "'${FALCON_CLIENT_ID}'", "falcon.client_secret": "'${FALCON_CLIENT_SECRET}'", "cloud.google.application_credentials": "'$GCLOUD_CREDS'" }'
   ```
 - review the logs fo the fig, make sure it is up and working
   ```
   kubectl logs -n test-ns "deploy/falcon-integration-gateway"
   ```
 - delete the namespace
   ```
   kubectl delete test-ns
   ```

## Verify the metadata of the application

```
mpdev verify \
      --deployer="$IMAGE:latest"
```

## Update the marketplace listing

Log in to GCP. Find producer portal. And follow the original documentation to update the marketplace listing: [Documentation](https://cloud.google.com/marketplace/docs/partners/kubernetes/maintaining-product).

