# Developer Guide

To understand the architecture, readers are advised to review [./fig/__main__.py](../fig/__main__.py). Central to the application is the event queue with one writer to the queue (Falcon module) and multiple readers from the queue (the worker threads). Falcon module maintains streaming session to CrowdStrike Falcon cloud and translates events from the streaming session to the internal queue. Once an event is put on queue it awaits its pickup by one of the worker threads. Worker thread iterates through enabled [backends](../fig/backends) and asks relevant backends to process the event.

## Getting Started

The easiest method to work on the FIG is to make use of a container environment, as this will ensure all dependencies are packaged within. Most backends have a corresponding developer guide with examples specific to the backend itself.

### Workflow

1. Fork and clone the repository
1. As changes are made to the code base, test them with the following approach:
    - Build the image

      ```bash
      docker build . -t falcon-integration-gateway
      ```

    - Run the application interactively passing in your [CONFIG](../config/config.ini) options as environment variables

      ```bash
      docker run -it --rm \
        -e FALCON_CLIENT_ID="$FALCON_CLIENT_ID" \
        -e FALCON_CLIENT_SECRET="$FALCON_CLIENT_SECRET" \
        -e FALCON_CLOUD_REGION="us-1" \
        -e FIG_BACKENDS=<BACKEND> \
        -e CONFIG_OPTION=CONFIG_OPTION_VALUE \
        falcon-integration-gateway:latest
      ```
