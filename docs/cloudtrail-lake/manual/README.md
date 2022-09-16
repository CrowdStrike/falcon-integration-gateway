# CloudTrail Lake - Manual Deployment
This guide provides a way to deploy the Falcon Integration Gateway from a container.
> :memo: This guide has been tested with Docker and Podman

## Prerequisites
- Falcon API Credentials
- AWS credentials configured on the host system
  > :warning: The aws account needs to have the [IAM Managed Policy](https://github.com/CrowdStrike/Cloud-AWS/tree/main/cloudtrail-lake#create-iam-managed-policy) permissions assigned to it

### Export the following variables
```bash
export FALCON_CLIENT_ID=<your api falcon client id>
export FALCON_CLIENT_SECRET=<your api falcon client secret>
export FALCON_CLOUD_REGION=<your api falcon client region>
export CLOUDTRAIL_LAKE_CHANNEL_ARN=<your cloudtrail lake channel arn>
export CLOUDTRAIL_LAKE_REGION=<your aws region aligning with channel>
export FALCON_APPLICATION_ID=<your unique application stream identifier>
export FIG_BACKENDS="CLOUDTRAIL_LAKE"
```

## Deployment
Using Docker in these examples, you can deploy the FIG as such:
> Refer to the [config.ini](https://github.com/CrowdStrike/falcon-integration-gateway/blob/main/config/config.ini) for
  more configuration options along with their respective ENV variable
#### In the example below, we are passing in our ~/.aws directory as our AWS credentials
```bash
docker run -d --rm
  -e FALCON_CLIENT_ID="$FALCON_CLIENT_ID" \
  -e FALCON_CLIENT_SECRET="$FALCON_CLIENT_SECRET" \
  -e FALCON_CLOUD_REGION="$FALCON_CLOUD_REGION" \
  -e FALCON_APPLICATION_ID="$FALCON_APPLICATION_ID" \
  -e FIG_BACKENDS="$FIG_BACKENDS" \
  -e CLOUDTRAIL_LAKE_CHANNEL_ARN="$CLOUDTRAIL_LAKE_CHANNEL_ARN" \
  -e CLOUDTRAIL_LAKE_REGION="$CLOUDTRAIL_LAKE_REGION" \
  -v ~/.aws:/fig/.aws quay.io/crowdstrike/falcon-integration-gateway:latest
```


#### You cloud also pass in your AWS credentials using ENV variables as such:
Export the following variables:
```bash
export AWS_ACCESS_KEY_ID=<The access key for your AWS account>
export AWS_SECRET_ACCESS_KEY=<The secret key for your AWS account>
```
Then pass in those variables to Docker:
```bash
docker run -d --rm
  -e FALCON_CLIENT_ID="$FALCON_CLIENT_ID" \
  -e FALCON_CLIENT_SECRET="$FALCON_CLIENT_SECRET" \
  -e FALCON_CLOUD_REGION="$FALCON_CLOUD_REGION" \
  -e FALCON_APPLICATION_ID="$FALCON_APPLICATION_ID" \
  -e FIG_BACKENDS="$FIG_BACKENDS" \
  -e CLOUDTRAIL_LAKE_CHANNEL_ARN="$CLOUDTRAIL_LAKE_CHANNEL_ARN" \
  -e CLOUDTRAIL_LAKE_REGION="$CLOUDTRAIL_LAKE_REGION" \
  -e AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
  -e AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
  quay.io/crowdstrike/falcon-integration-gateway:latest
```

## Verify
To verify deployment, check the log of the container:
```bash
docker logs <container>
```
Example output:
```bash
2022-09-16 21:14:40 fig MainThread INFO     AWS CloudTrail Lake Backend is enabled.
2022-09-16 21:14:42 fig cs_stream  INFO     Opening Streaming Connection
```
## Upgrade
To upgrade the container, stop any existing running FIG containers and run the following:
```bash
docker pull quay.io/crowdstrike/falcon-integration-gateway
```
