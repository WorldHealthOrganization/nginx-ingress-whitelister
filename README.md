# Envoy Gateway - Fingerprint whitelisting and Creation of Gateway CA bundle for MTLS

> Automated certificate whitelisting and pinning for Envoy Gateway with Kubernetes integration


## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Scripts Documentation](#scripts-documentation)
- [Kubernetes Resources](#kubernetes-resources)
- [Monitoring & Troubleshooting](#monitoring--troubleshooting)
- [FAQ](#faq)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

The **Envoy Gateway Fingerprint Whitelister ** is a Kubernetes-native solution that automates client certificate validation for Envoy Gateway deployments. This project simplifies the complex setup of mutual TLS (mTLS) authentication by automatically:

- **Managing CA Bundles** from certificate repositories
- **Generating Certificate Fingerprints** for pinning
- **Updating ClientTrafficPolicy** resources automatically
- **Scheduling Updates** via Kubernetes CronJobs
- **Cleaning Up Resources** on uninstall


## ✨ Features

- ✅ **Automatic CA Bundle Creation** - Aggregates certificates from any Git repository
- ✅ **Certificate Fingerprint Pinning** - Generates SHA256 fingerprints for certificate validation
- ✅ **Envoy ClientTrafficPolicy Integration** - Seamlessly updates Envoy Gateway policies
- ✅ **Scheduled Updates** - Configurable CronJob for automatic certificate refreshes
- ✅ **Kubernetes-Native** - Uses standard K8s primitives (Secrets, ConfigMaps, CronJobs)
- ✅ **RBAC Compliant** - Minimal, scoped permissions
- ✅ **Automated Cleanup** - Helm pre-delete hooks for safe uninstall
- ✅ **Certificate Validation** - Validates certificate integrity before deployment
- ✅ **Comprehensive Logging** - Detailed logs for troubleshooting

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Certificate Repository                    │
│              (Git repo with TLS certificates)               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Kubernetes CronJob (Bot)                    │
│  - Clones certificate repository                            │
│  - Validates certificates                                   │
│  - Generates fingerprints (fingerprints.sh)               │
│  - Updates CA Bundle (updateCaBundle.py)                   │
│  - Updates ClientTrafficPolicy (updateFingerprints.py)    │
└────────┬──────────────────────┬──────────────────────────────┘
         │                      │
         ▼                      ▼
┌──────────────────┐  ┌──────────────────────┐
│  K8s Secret      │  │ ClientTrafficPolicy  │
│ (CA Certificate) │  │  (Fingerprints)      │
└────────┬─────────┘  └──────────┬───────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
         ┌──────────────────────┐
         │  Envoy Gateway       │
         │  - Validates client  │
         │    certificates      │
         │  - Pins fingerprints │
         └──────────────────────┘
```

## 📋 Prerequisites

- **Kubernetes Cluster**: 1.20 or higher
- **Helm**: 3.0 or higher
- **Envoy Gateway**: Deployed and running
- **ClientTrafficPolicy**: Is present in the cluster
- **Git**: For cloning certificate repositories
- **OpenSSL**: For certificate validation (included in Alpine images)
- **Python 3**: For running update scripts
- **Kubernetes Service Account**: With appropriate RBAC permissions

### Required Python Packages

```
kubernetes
gitpython
cryptography
```

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/WorldHealthOrganization/nginx-ingress-whitelister.git
cd nginx-ingress-whitelister
git checkout envoy
```

### 2. Prepare Configuration

Create a `values.yaml` file:

```yaml
config:
  repo: https://github.com/WorldHealthOrganization/nginx-ingress-whitelister.git
  tag: envoy

bundle:
  name: gateway-ca-bundle-envoy
  namespace: default
  repo: https://github.com/YOUR-ORG/YOUR-CERT-REPO.git

clienttrafficpolicy:
  name: xfcc-policy
  namespace: default

job:
  schedule: '*/60 * * * *'  # Every 60 minutes
```

### 3. Install with Terraform Helm resouce via tng-iac

### 4. Verify Installation

```bash
# Check deployment
kubectl get cronjob -n default
kubectl get secret -n default | grep gateway-ca-bundle-envoy
kubectl get clienttrafficpolicy -n default

# View logs
kubectl logs -n envoy-gateway-system -l app=gateway-whitelister
```

## ⚙️ Configuration

### Helm Values

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config.repo` | string | `https://github.com/WorldHealthOrganization/nginx-ingress-whitelister.git` | Git repository URL with whitelisting code |
| `config.tag` | string | `envoy` | Git branch/tag to checkout |
| `bundle.repo` | string | - | Git repository URL containing certificates |
| `bundle.name` | string | `gateway-ca-bundle-envoy` | Kubernetes Secret name for CA bundle |
| `bundle.namespace` | string | `default` | Namespace where CA Secret is stored |
| `clienttrafficpolicy.name` | string | `xfcc-policy` | ClientTrafficPolicy resource name |
| `clienttrafficpolicy.namespace` | string | `default` | Namespace of ClientTrafficPolicy |
| `job.schedule` | string | `*/60 * * * *` | CronJob schedule (Unix Cron format) |

### Example values.yaml

```yaml
config:
  repo: https://github.com/WorldHealthOrganization/nginx-ingress-whitelister.git
  tag: envoy

bundle:
  name: gateway-ca-bundle-envoy
  namespace: default
  repo: https://github.com/WorldHealthOrganization/tng-participants-dev.git

clienttrafficpolicy:
  name: xfcc-policy
  namespace: default

job:
  schedule: '*/60 * * * *'
```

### Environment Variables

When the CronJob executes, these environment variables are passed to the scripts:

| Variable | Source | Description |
|----------|--------|-------------|
| `TAG` | values.yaml | Git branch to checkout |
| `REPO` | values.yaml | Git repository URL |
| `CERTIFICATEFOLDER` | values.yaml | Certificate repository URL |
| `BUNDLE_NAMESPACE` | values.yaml | Target namespace for CA Secret |
| `BUNDLE_NAME` | values.yaml | Target Secret name |
| `POLICY_NAME` | values.yaml | ClientTrafficPolicy name |
| `POLICY_NAMESPACE` | values.yaml | ClientTrafficPolicy namespace |

## 📖 Usage

### Automatic Updates (CronJob)

The system runs on a schedule defined in `job.schedule`. Each execution:

1. Clones the certificate repository
2. Validates all certificates
3. Generates fingerprints
4. Updates the CA Bundle Secret
5. Updates the ClientTrafficPolicy with fingerprints

### Manual Trigger

To manually run the update job:

```bash
# Create a one-off job from the CronJob template
kubectl create job --from=cronjob/<cronjob name> \
  manual-update \
  -n envoy-gateway-system
```

### Update ClientTrafficPolicy Manually

If you need to manually update the policy:

```bash
# View current policy
kubectl get clienttrafficpolicy xfcc-policy -n default -o yaml

# Edit the policy
kubectl patch clienttrafficpolicy xfcc-policy -n default --type merge \
  -p '{"spec":{"tls":{"clientValidation":{"certificateHashes":["hash1","hash2"]}}}}'
```

## 🔧 Scripts Documentation

### fingerprints.sh

Extracts SHA256 certificate fingerprints from PEM files.

**Usage:**
```bash
./fingerprints.sh <search_directory>
```

**Inputs:**
- `search_directory`: Path to search for certificates (recursively) certifactes directory

**Outputs:**
- `<search_dir>/hashes_list`: File containing fingerprints (one per line)
- `<search_dir>/invalid`: File listing invalid certificates

**Example:**
```bash
./fingerprints.sh ./certificateFolder
cat ./certificateFolder/hashes_list
```

### updateCaBundle.py

Creates/updates a Kubernetes Secret with CA certificates.

**Usage:**
```bash
python updateCaBundle.py 
```

**Environment Variables:**
- `BUNDLE_NAMESPACE`: Target namespace (required)
- `BUNDLE_NAME`: Secret name (required)

**Process:**
1. Finds all `CA*.pem` files in `./certificateFolder/TLS/`
2. Validates certificate format
3. Creates base64-encoded bundle
4. Updates/patches Kubernetes Secret

**Example:**
```bash
export BUNDLE_NAMESPACE=default
export BUNDLE_NAME=gateway-ca-bundle
python updateCaBundle.py
```

### updateFingerprints.py

Updates ClientTrafficPolicy with certificate fingerprints.

**Usage:**
```bash
python updateFingerprints.py <fingerprints_file>
```

**Arguments:**
- `fingerprints_file`: Path to file containing fingerprints (from fingerprints.sh)

**Environment Variables:**
- `POLICY_NAME`: ClientTrafficPolicy resource name (required)
- `POLICY_NAMESPACE`: Namespace of policy (optional, default: default)

**Process:**
1. Fetches existing ClientTrafficPolicy
2. Reads fingerprints from file
3. Updates `spec.tls.clientValidation.certificateHashes`
4. Patches the resource back

**Example:**
```bash
export POLICY_NAME=xfcc-policy
export POLICY_NAMESPACE=default
python updateFingerprints.py ./certificateFolder/hashes_list
```

## 🐳 Kubernetes Resources

### Service Account & RBAC

The chart creates:
- **ServiceAccount**: `gateway-whitelister-service-account`
- **ClusterRole**: 
  - `gateway-whitelister-controller`: Permissions to read/patch ClientTrafficPolicy
  - `gateway-whitelister-rule`: Permissions to read/patch Secrets and ConfigMaps
- **ClusterRoleBinding**: Links roles to service account

### Secrets & ConfigMaps

- **Secret `gateway-ca-bundle`**: Contains base64-encoded CA certificates
- **ConfigMap `gateway-whitelister-bot-config`**: Contains the update script

### CronJob

- **CronJob `gateway-whitelister-bot`**: Executes update job on schedule
- **Job `gateway-whitelister-bot-delete-hook`**: Cleanup on Helm uninstall

## 📊 Monitoring & Troubleshooting

### View Pod Logs

```bash
# Latest CronJob execution
kubectl logs -n envoy-gateway-system -l batch.kubernetes.io/job-name=gateway-whitelister-bot-* --tail=100

# Watch logs in real-time
kubectl logs -f -n envoy-gateway-system -l batch.kubernetes.io/job-name=gateway-whitelister-bot-* --all-containers=true
```
