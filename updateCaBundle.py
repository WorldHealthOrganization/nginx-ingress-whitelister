import os
import glob
import base64
import logging
import datetime
import sys
from kubernetes import client, config
from cryptography import x509
from cryptography.hazmat.backends import default_backend

# -------------------------------------------------------------------
# Logging configuration
# -------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s"
)
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Kubernetes client setup
# -------------------------------------------------------------------
try:
	config.load_incluster_config()
except Exception as e:
    logger.error(f"Failed to load kubeconfig: {e}")
    sys.exit(1)

bundle_namespace = os.environ.get("BUNDLE_NAMESPACE")
bundle_name=os.environ.get("BUNDLE_NAME")

if not bundle_namespace:
  logger.error("Environment variables BUNDLE_NAMESPACE must be set")
  sys.exit(1)
if not bundle_name:
  logger.error("Environment variables BUNDLE_NAME must be set")
  sys.exit(1)

def is_valid_certificate(content, file):
  try:
    cert = x509.load_pem_x509_certificate(content.encode("utf-8"), default_backend())
    #cert = x509.load_pem_x509_certificate(content, default_backend())
    expiry = cert.not_valid_after_utc
    now = datetime.datetime.now(datetime.timezone.utc)
    days_left = (expiry - now).days

    if days_left < 0:
      logger.error(f"CA cert {file} is expired on {expiry.strftime('%Y-%m-%d %H:%M:%S UTC')} will not add to Gateway CA bundle, renew the CA certificate")
      return False
    elif days_left < 30:
      logger.warning(f"CA cert {file} will expire in {days_left} days, Kindly get the certs renewed")
      return True
    else:
      logger.debug(f"CA cert {file} is valid")
      return True

  except ValueError as e:
    logger.error(f"Error processing CA cert {file} :: {e}")
    return False
  except Exception as e:
    logger.error(f"Error processing CA cert {file} :: {e}")
    return False

files = glob.glob("./certificateFolder/**/TLS/CA*.pem", recursive=True)
ca_bundle = ""

error_count = 0
processed_count = 0

for file in files:
  logger.debug(f"Processing CA certificate {file}")
  with open(file, "r") as f:
    data = f.read()
  if is_valid_certificate(data, file):
    ca_bundle = ca_bundle+"\n"+data
    processed_count+=1
  else:
    error_count+=1

if len(files) and ca_bundle:
  api_instance = client.CoreV1Api()
  body = client.V1Secret()
  body.api_version = 'v1'
  body.data = {'ca.crt': str(base64.b64encode(bytes(ca_bundle,"utf-8")),"utf-8")}
  body.kind = 'Secret'
  body.type = 'Opaque'

  #print(ca_bundle)
  api_instance.patch_namespaced_secret(namespace=bundle_namespace,name=bundle_name, body=body)
  logger.info(f"Successfully added {processed_count} CA certificates to {bundle_name} and failed processing {error_count} CA certificates")
  if error_count > 0:
    logger.info("Look for error messages and fix the issue as per the logged error message. Countries with Failures would not be able to establish connection via Envoy Gateway")
else:
  logger.warning("No files found or empty CA bundle")
