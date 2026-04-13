# Deployment Instructions

This guide details the steps to deploy the "Healthcare Clinical Trial Matcher" infrastructure on a fresh Google Cloud Project using GCP Cloud Shell.

## Prerequisites

1. **Select Project:** Ensure you have selected the correct project in Cloud Shell:
```bash
gcloud config set project $PROJECT_ID
```

2. **Clone Repository:** Clone this repository in Cloud Shell to get the manifests and scripts:
```bash
git clone https://github.com/mtoscano84/healthcare-trail-matcher-ai.git
cd healthcare-trail-matcher-ai
```

## 1. Enable Required APIs

Enable the APIs required for GKE and networking:
```bash
gcloud services enable \
    container.googleapis.com \
    compute.googleapis.com
```

## 2. Create Custom VPC Network

Since we cannot use the default network, we will create a custom VPC and subnet:

```bash
export REGION=us-central1
export NETWORK_NAME=sovereign-ai-net
export SUBNET_NAME=sovereign-ai-subnet

# Create VPC network
gcloud compute networks create $NETWORK_NAME --subnet-mode=custom

# Create subnet
gcloud compute networks subnets create $SUBNET_NAME \
    --network=$NETWORK_NAME \
    --range=10.0.0.0/24 \
    --region=$REGION
```

## 3. Create GKE Cluster

Create the GKE cluster referencing the custom network and subnet:
```bash
export CLUSTER_NAME=sovereign-ai-cluster

gcloud container clusters create $CLUSTER_NAME \
    --project=$PROJECT_ID \
    --region=$REGION \
    --num-nodes=3 \
    --machine-type=e2-standard-4 \
    --enable-ip-alias \
    --network=$NETWORK_NAME \
    --subnetwork=$SUBNET_NAME \
    --scopes="https://www.googleapis.com/auth/cloud-platform"
```

## 4. Install AlloyDB Omni Operator

Install the operator that manages the AlloyDB Omni database in the cluster:
```bash
# Get cluster credentials
gcloud container clusters get-credentials $CLUSTER_NAME --region $REGION --project $PROJECT_ID

# Configure Docker auth for GCR
gcloud auth configure-docker gcr.io

# Login to Helm registry
gcloud auth print-access-token | helm registry login -u oauth2accesstoken --password-stdin gcr.io

# Install Operator
helm install alloydbomni-operator oci://gcr.io/alloydb-omni/alloydbomni-operator \
    --version 1.7.0 \
    --create-namespace \
    --namespace alloydb-omni-system \
    --atomic \
    --timeout 5m
```

## 5. Generate and Load Data

Generate synthetic healthcare data and load it into the database:

```bash
# Create namespace for data
kubectl create namespace data

# Generate data (creates CSVs in data/ directory)
python3 src/generate_data.py

# Create ConfigMap with the CSV files
kubectl create configmap clinical-data --from-file=data/ -n data

# Deploy AlloyDB Cluster
kubectl apply -f k8s/alloydb-cluster.yaml

# Run the data loading job
kubectl apply -f k8s/data-load-job.yaml
```
