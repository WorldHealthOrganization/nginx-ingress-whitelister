#!/bin/sh

# --- Validate input ---
if [[ $# -lt 1 ]]; then
    echo "Usage: $(basename "$0") <search_dir>" >&2
    exit 1
fi

search_dir="$1"

if [[ ! -d "$search_dir" ]]; then
    echo "Error: '$search_dir' is not a directory." >&2
    exit 1
fi

# --- Output files (truncated on each run) ---
hashes="${search_dir}/hashes_list"
invalid_certs="${search_dir}/invalid"
> "$hashes"
> "$invalid_certs"

# --- Process certificates ---
for cert in $(/usr/bin/find $1 -path **/TLS/* -name TLS*.pem)
do
    #fingerprint=$(
    #    openssl x509 -in "$cert" -noout -fingerprint -sha256 | sed 's/.*Fingerprint=//; s/://g'
    #)
    fingerprint=$(openssl x509 -in "$cert" -noout -fingerprint -sha256 | sed 's/sha256 Fingerprint=//;s/sha256 Fingerprint=//; s/://g')

    # Expect exactly 64 hex characters; reject empty / malformed output
    if [ "$(echo -n "$fingerprint" | wc -m)" -eq 64 ]; then
        echo "$fingerprint" >> "$hashes"
    else
        printf '## Invalid fingerprint: %s\n' "$cert" >> "$invalid_certs"
    fi
done
