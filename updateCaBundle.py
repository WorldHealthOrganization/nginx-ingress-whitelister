import os
import glob
import base64
import re
from kubernetes import client, config

config.load_incluster_config()

bundle_namespace = os.environ.get("BUNDLE_NAMESPACE")
bundle_name = os.environ.get("BUNDLE_NAME")

# Cert validation function
def is_valid_pem_cert(content):
  pem_pattern = re.compile(
      r"-----BEGIN CERTIFICATE-----\s+([a-zA-Z0-9+/=\s]+)\s+-----END CERTIFICATE-----",
      re.DOTALL
  )
  match = pem_pattern.search(content)
  if not match:
      return False
  try:
      base64.b64decode(match.group(1), validate=True)
      return True
  except base64.binascii.Error:
      return False

files = glob.glob("./certificateFolder/**/TLS/CA*.pem", recursive=True)
ca_bundle = ""
for file in files:
  with open(file) as f:
    data = f.read()
  if is_valid_pem_cert(data):
      ca_bundle += "\n" + data
  else:
      print(f"Skipping invalid certificate file: {file}")
  
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
    
