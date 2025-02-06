import os
import glob
import base64
from kubernetes import client, config
from cryptography import x509
from cryptography.hazmat.backends import default_backend

config.load_incluster_config()

bundle_namespace = os.environ.get("BUNDLE_NAMESPACE")
bundle_name=os.environ.get("BUNDLE_NAME")

def is_valid_certificate(content):
  try:
    x509.load_pem_x509_certificate(content.encode("utf-8"), default_backend())
    return True
  except Exception:
    return False

files = glob.glob("./certificateFolder/**/TLS/CA*.pem", recursive=True)
ca_bundle = ""

for file in files:
  with open(file, "r") as f:
    data = f.read()
  if is_valid_certificate(data):
    ca_bundle = ca_bundle+"\n"+data
  else:
    print("Skipping invalid certificate file: {file}")
    
if len(files) and ca_bundle:
  api_instance = client.CoreV1Api()
  body = client.V1Secret()
  body.api_version = 'v1'
  body.data = {'ca.crt': str(base64.b64encode(bytes(ca_bundle,"utf-8")),"utf-8")}
  body.kind = 'Secret'
  body.type = 'Opaque'
  api_instance.patch_namespaced_secret(namespace=bundle_namespace,name=bundle_name, body=body)
else: 
  print("No files found or empty CA bundle")
