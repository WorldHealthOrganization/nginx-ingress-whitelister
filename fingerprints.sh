#!/bin/bash

nginx_conf="$1/nginx_conf"

echo 'map $ssl_client_fingerprint $reject {' >> $nginx_conf
echo "default 1;" >> $nginx_conf

for cert in $(/usr/bin/find $1 -path **/TLS/* -name TLS*.pem)
do
    fingerprint=$(openssl x509 -in "$cert" -noout -fingerprint -sha1 | sed 's/SHA1 Fingerprint=//;s/sha1 Fingerprint=//; s/://g')
    # Check to prevent whitelisting empty certs
    if [ "$(echo -n "$fingerprint" | wc -m)" -eq 40 ]; then
        echo "$fingerprint 0;" >> "$nginx_conf"
    else
        echo "##Invalid fingerprint: $cert" >> "$nginx_conf"
    fi
done

echo "}" >> $nginx_conf
