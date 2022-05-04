# Falcon Integration Gateway for Chronicle - Deployment Guide to Kubernetes

This guide works through deployment of Falcon Integration Gateway for Chronicle to kubernetes. Only the Chronicle [backend](https://github.com/CrowdStrike/falcon-integration-gateway/tree/main/fig/backends) will be enabled by this guide.

### Prerequisites:

 - Have CrowdStrike CWP Subscription
 - Have Chronicle subscription

### Step 1: Create new CrowdStrike API Key Pairs

Create new API key pair at [CrowdStrike Falcon](https://falcon.crowdstrike.com/support/api-clients-and-keys). This key pair will be used to read falcon events and supplementary information from CrowdStrike Falcon.

Make sure only the following permissions are assigned to the key pair:
 * Event streams: READ
 * Hosts: READ

### Step 2: Obtain Chronicle Service Account file. 

Your Chronicle Support representative will provide you with a JSON Service Account file. This file will need to be in the path specified in the pod spec.

### Step 3: Edit kubernetes pod spec

Kubernetes pod specification file is readily available at [https://github.com/CrowdStrike/falcon-integration-gateway](falcon-integration-gateway.yaml).

```
wget https://raw.githubusercontent.com/crowdstrike/falcon-integration-gateway/main/docs/chronicle/falcon-integration-gateway.yaml
```

Replace the credentials in the pod spec with the actual Falcon and Chronicle credentials created in the previous steps. To following commands illustrate how to base64 encode the credentials.

```
echo -n $FALCON_CLIENT_ID | base64
```

```
echo -n $FALCON_CLIENT_SECRET | base64
```

```
echo -n $GOOGLE_CUSTOMER_ID | base64
```

Set the region of your Chronicle cloud.

```
    # Uncomment to provide Chronicle region (us, europe, asia-southeast1). Alternatively, use CHRONICLE_REGION variable
    region = us
```

### Step 5: Deploy to kubernetes

Ensure your kubectl command is configured to use kubernetes
```
kubectl cluster-info
```

Deploy the pod
```
kubectl apply -f falcon-integration-gateway.yaml
```
