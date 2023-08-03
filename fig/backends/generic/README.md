# Generic Backend

Generic backend is useful for testing and development purposes. It is not recommended for production use.

## Example Configuration file

[config/config.ini](https://github.com/CrowdStrike/falcon-integration-gateway/blob/main/config/config.ini) configures Falcon Integration Gateway. Below is a minimal configuration example for GENERIC backend:

```terminal
[main]
# Cloud backends that are enabled. The gateway will push events to the cloud providers specified below
backends=GENERIC
```

## Developer Guide

1. Build the image

    ```shell
    docker build . -t falcon-integration-gateway
    ```

1. Run the application

    ```shell
    docker run -it --rm \
        -e FALCON_CLIENT_ID="$FALCON_CLIENT_ID" \
        -e FALCON_CLIENT_SECRET="$FALCON_CLIENT_SECRET" \
        -e FALCON_CLOUD_REGION="us-1" \
        falcon-integration-gateway:latest
    ```
