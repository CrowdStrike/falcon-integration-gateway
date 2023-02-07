# GKE Marketplace Listing

GKE marketplace listing consists of 4 parts:
 - application container
 - helm chart and the deployer metadata (in this directory)
 - deployer container (responsible for distributing and deploying the helm chart)
 - marketplace ui representation

Please consult GCP documentation below to understand the topic of marketplace listings more broadly.
 - [Requirement for packaging your app](https://cloud.google.com/marketplace/docs/partners/kubernetes/create-app-package)
 - [Deployer Schema](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/blob/master/docs/schema.md#x-google-marketplace-1)
 - [How to build deployer image: Step 1](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/blob/master/docs/building-deployer.md)
 - [How to build deployer image: Step 2](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/blob/master/docs/building-deployer-helm.md)
 - [How to install published marketplace application manually](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/blob/master/docs/mpdev-references.md#installing-a-published-marketplace-app)

## How to update the marketplace listing

### Preparation
- A new version of the FIG application image has been built/pushed to Quay.io registry
    > This generally happens when a new release of FIG is published
- authenticate with GCP using gcloud
  > login to the ***CrowdStrike-public*** GCP project
- create your [GKE cluster](https://cloud.google.com/kubernetes-engine/docs/deploy-app-cluster#create_cluster) for testing, configure your kubectl command to use that cluster
  ```shell
  gcloud container clusters create-auto example-fig-cluster1 --region us-central1
  ```
- install [mpdev](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/blob/master/docs/tool-prerequisites.md) command locally

### Push the application image

1. Pull the FIG released application image from quay builder
    ```shell
    docker pull quay.io/crowdstrike/falcon-integration-gateway:latest
    ```
    > Make note of the image id, you will need it in the next step
1. Push new version of the application image to `gcr.io/crowdstrike-public/falcon-integration-gateway`
   1. Tag the pushed image with 3 tags, similar to following: `latest`, `3.1`, and `3.1.X`
    ```shell
    docker tag <image_id> gcr.io/crowdstrike-public/falcon-integration-gateway:latest
    docker tag <image_id> gcr.io/crowdstrike-public/falcon-integration-gateway:3.1
    docker tag <image_id> gcr.io/crowdstrike-public/falcon-integration-gateway:3.1.<latest release>
    ```
   1. Push the image to the registry
    ```shell
    docker image push --all-tags gcr.io/crowdstrike-public/falcon-integration-gateway
    ```

### Build and Push the deployer image

1. Refresh deployer base container locally
    ```shell
    docker pull gcr.io/cloud-marketplace-tools/k8s/deployer_helm/onbuild
    ```
1. Build and tag the image accordingly with 3 tags, similar to the following: `latest`, `3.1`, `3.1.X`
    > Navigate to the `docs/listings/gke/deployer` directory before running the following commands
    ```shell
    docker build --tag gcr.io/crowdstrike-public/falcon-integration-gateway/deployer:latest .
    # Make note of the image id
    docker image tag <image_id> gcr.io/crowdstrike-public/falcon-integration-gateway/deployer:3.1
    docker image tag <image_id> gcr.io/crowdstrike-public/falcon-integration-gateway/deployer:3.1.<latest release>
    ```
1. Push the image to the registry
    ```shell
    docker image push --all-tags gcr.io/crowdstrike-public/falcon-integration-gateway/deployer
    ```

### Test the deployer and the application

- Create namespace
    ```
    kubectl create namespace test-ns
    ```
- Deploy the application
    > If you don't have a service account for this step, refer to step 2 of the [user guide](UserGuide.md) to configure one
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

### Troubleshooting
If you see the following error message when running the mddev install command:
```
...
Using /opt/kubectl/1.23/kubectl (server=1.23)
Using /opt/kubectl/1.23/kubectl (server=1.23)
error: unable to recognize "STDIN": no matches for kind "Application" in version "app.k8s.io/v1beta1"
```
Then execute the following command to install the Application CRD:
```shell
kubectl apply -f "https://raw.githubusercontent.com/GoogleCloudPlatform/marketplace-k8s-app-tools/master/crd/app-crd.yaml"
```

### Verify the metadata of the application

```
mpdev verify \
      --deployer="$IMAGE:latest"
```

## Update the marketplace listing

Log in to GCP. Find producer portal. And follow the original documentation to update the marketplace listing: [Documentation](https://cloud.google.com/marketplace/docs/partners/kubernetes/maintaining-product).
