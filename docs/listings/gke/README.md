# GKE Marketplace Listing

## Developer Links

 - GCP Documentation
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
      --deployer=$REGISTRY/$APP_NAME/deployer \

```
