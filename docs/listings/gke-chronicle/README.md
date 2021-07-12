# GKE Marketplace Listing

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
      --parameters='{"name": "falcon-integration-gateway", "namespace": "test-ns", "falcon.cloud_region": "us-1", "falcon.client_id": "'${client_id}'", "falcon.client_secret": "'${client_secret}'", "chronicle.google_security_key": "'$chronicle_creds'" }'
```

## How to run sanity test?
```
mpdev verify \
      --deployer=$REGISTRY/$APP_NAME/deployer
```

## How to update marketplace listing?

[Documentation](https://cloud.google.com/marketplace/docs/partners/kubernetes/maintaining-product)

### Minor version updates

For every update, you need to push the latest deployer image to the staging repo and update the patch version of your listing (e.g., '3.0.4', '3.0.5'). The update would contain new content, and therefore must have a bumped version number. Once updated, please click the "Update images" button in Partner Portal, and resubmit your draft for a review. Let me know if you have any questions.
