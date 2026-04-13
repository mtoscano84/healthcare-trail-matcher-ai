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

## 2. Create Custom VPC Network and Cloud NAT

Since we cannot use the default network and must comply with strict organization policies (no external IPs, shielded VMs required), we will create a custom VPC, a subnet with Private Google Access, and a Cloud NAT gateway to allow private nodes to pull external images (like cert-manager from quay.io).

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
    --region=$REGION \
    --enable-private-ip-google-access

# Create Cloud Router (required for NAT)
gcloud compute routers create sovereign-ai-router \
    --network=$NETWORK_NAME \
    --region=$REGION

# Create Cloud NAT Gateway
gcloud compute routers nats create sovereign-ai-nat \
    --router=sovereign-ai-router \
    --region=$REGION \
    --auto-allocate-nat-external-ips \
    --nat-all-subnet-ip-ranges
```

## 3. Create GKE Cluster

Create the GKE cluster referencing the custom network. We enable **Private Nodes** and **Shielded VM Secure Boot** to comply with your project's organization policies:

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
    --enable-private-nodes \
    --master-ipv4-cidr=172.16.0.0/28 \
    --enable-shielded-nodes \
    --shielded-secure-boot \
    --shielded-integrity-monitoring \
    --scopes="https://www.googleapis.com/auth/cloud-platform"
```
> [!NOTE]
> We are creating a cluster with private nodes but a **public master endpoint**. This allows you to manage the cluster directly from Cloud Shell without setting up a VPN or Bastion host, while still ensuring the nodes themselves have no external IP addresses.

## 4. Verify and Authorize Cluster Connection

Before proceeding, you must authorize your Cloud Shell environment to connect to the GKE master endpoint and verify the connection:

```bash
# 1. Get cluster credentials
gcloud container clusters get-credentials $CLUSTER_NAME --region $REGION --project $PROJECT_ID

# 2. Find your Cloud Shell Public IP
export CLOUD_SHELL_IP=$(curl -s ifconfig.me)
echo "Cloud Shell IP: $CLOUD_SHELL_IP"

# 3. Authorize Cloud Shell IP in GKE (required due to Org Policies)
gcloud container clusters update $CLUSTER_NAME \
    --region=$REGION \
    --enable-master-authorized-networks \
    --master-authorized-networks=$CLOUD_SHELL_IP/32

# 4. Check node status
kubectl get nodes
```
You should see your nodes in the `Ready` status.

## 5. Install cert-manager

The AlloyDB Omni operator requires **cert-manager** to be installed. We also need to add a firewall rule to allow the GKE master to talk to the cert-manager webhook on port 9443.

Run these commands to install it:

```bash
# 1. Create firewall rule for webhook
gcloud compute firewall-rules create allow-gke-master-to-cert-manager \
    --network=$NETWORK_NAME \
    --allow=tcp:9443 \
    --source-ranges=172.16.0.0/28 \
    --description="Allow GKE master to reach cert-manager webhook"

# 2. Add the Jetstack Helm repository
helm repo add jetstack https://charts.jetstack.io
helm repo update

# 3. Install cert-manager Helm chart
helm install cert-manager jetstack/cert-manager \
    --namespace cert-manager \
    --create-namespace \
    --version v1.14.4 \
    --set installCRDs=true

# 4. Wait for cert-manager to be ready
kubectl wait --for=condition=Available deployment --all -n cert-manager --timeout=300s
```

## 6. Install AlloyDB Omni Operator

Now you can install the operator that manages the AlloyDB Omni database:
```bash
# Configure Docker auth for GCR
gcloud auth configure-docker gcr.io

# Login to Helm registry
gcloud auth print-access-token | helm registry login -u oauth2accesstoken --password-stdin gcr.io

# Install Operator
helm install alloydbomni-operator oci://gcr.io/alloydb-omni/alloydbomni-operator \
    --version 1.7.0 \
    --create-namespace \
    --namespace alloydb-omni-system \
    --rollback-on-failure \
    --timeout 5m
```

## 7. Generate and Load Data

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

## 8. Verify Database and Data

Verify that the database is ready and data has been loaded successfully:

```bash
# 1. Check Database Status (Should show Ready and DBClusterReady)
kubectl get dbcluster -n data

# 2. Check Data Loader Job Logs
kubectl logs -l job-name=data-loader -n data

# 3. (Optional) Verify row counts in the database
# This runs a temporary pod to connect and count patients
kubectl run -i --tty --rm psql-client --image=postgres:15 -n data --env="PGPASSWORD=alloydb" -- \
   psql -h al-healthcare-db-rw-ilb -U postgres -d healthcaredb -c "SELECT COUNT(*) FROM patients;"
```

## 9. Deploy Reasoning Engine (Ollama)

Deploy Ollama to serve the Gemma model for our reasoning engine:

```bash
# Create namespace for AI inference
kubectl create namespace ai-inference

# Deploy Ollama (Deployment and Service)
kubectl apply -f k8s/ollama.yaml

# Verify deployment
kubectl get pods -n ai-inference
```
> [!NOTE]
> The deployment includes a post-start hook to automatically pull the `gemma:2b` model. The pod might take a few minutes to show as `Ready` while it downloads the model.

## 10. Verify Reasoning Engine

Test that the LLM is working by executing a prompt directly inside the container:

```bash
kubectl exec -it $(kubectl get pod -l app=ollama -n ai-inference -o jsonpath='{.items[0].metadata.name}') -n ai-inference -- ollama run gemma:2b "Why is the sky blue?"
```
If successful, you should see the AI response streaming in your terminal.

## 11. Deploy MCP Toolbox Bridge

Build and deploy the MCP Toolbox to expose database tools to the agent. We use Artifact Registry as GCR is deprecated.

```bash
# 1. Create namespace for MCP
kubectl create namespace mcp-server

# 2. Enable Artifact Registry API and create repo
gcloud services enable artifactregistry.googleapis.com
gcloud artifacts repositories create healthcare-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="Healthcare AI repo"

# 3. Grant Artifact Registry Reader role to GKE default service account
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/artifactregistry.reader"

# 4. Build and push the image
gcloud auth configure-docker us-central1-docker.pkg.dev
docker build -t us-central1-docker.pkg.dev/$PROJECT_ID/healthcare-repo/mcp-toolbox:latest .
docker push us-central1-docker.pkg.dev/$PROJECT_ID/healthcare-repo/mcp-toolbox:latest

# 5. Deploy the MCP Toolbox
kubectl apply -f k8s/mcp-toolbox.yaml
```

### Validation

Verify that the MCP server started correctly and loaded the tools:

```bash
kubectl logs -l app=mcp-toolbox -n mcp-server
```

You should see output similar to:
```
INFO "Initialized 1 sources: healthcare-db"
INFO "Initialized 4 tools: search_patients_by_condition, get_patient_profile, get_patient_conditions, get_patient_treatments"
INFO "Server ready to serve!"
```
