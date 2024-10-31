#!/usr/bin/env python3

import yaml
import json
import argparse
from tqdm import tqdm
from ultra_rest_client.connection import RestApiConnection
from parser import parse_yaml
from helper import check_for_a, check_for_cname, get_webforward_guid

# Set up argument parser
parser = argparse.ArgumentParser(
    description="Script for managing atomic modifications of UltraDNS web forwards and rrsets through batch requests."
)

parser.add_argument(
    "-y", "--yaml",
    type=str,
    default="config.yml",
    help="Path to the YAML configuration file (default: config.yml in the current working directory)."
)

args = parser.parse_args()

# Load YAML configuration
with open(args.yaml, "r") as file:
    config = yaml.safe_load(file)

# Extract credentials
username = config["username"]
password = config["password"]

# Parse the YAML to obtain a structured list of domains
parsed_domains = parse_yaml(config, tqdm)

# Initialize UltraDNS client
client = RestApiConnection(host='api.ultradns.com')
client.auth(username, password)

# Initialize list to store operation messages
messages = []

# Main Logic
for domain_data in tqdm(parsed_domains, desc="Processing domains"):
    domain_name = domain_data["domain"]

    # Process rrsets from YAML
    for rrset in tqdm(domain_data["rrsets"], desc=f"Iterating through rrsets in {domain_name}", leave=False):
        host = rrset["host"]
        full_host_name = f"{domain_name}" if host is None else f"{host}.{domain_name}"
        rdata = rrset["rdata"]
        rtype = rrset["rtype"]
        ttl = rrset["ttl"]

        # Step 1: Check if a web forward exists for this hostname
        guid = get_webforward_guid(domain_name, full_host_name, client)
        if guid:
            # If a web forward exists, delete it and add the rrset
            batch_request = [
                {"method": "DELETE", "uri": f"/v3/zones/{domain_name}/webforwards/{guid}"},
                {
                    "method": "POST",
                    "uri": f"/v1/zones/{domain_name}/rrsets/{rtype}/{host if host else domain_name}",
                    "body": {
                        "ttl": ttl,
                        "rdata": [rdata] if not isinstance(rdata, list) else rdata
                    }
                }
            ]
            response = client.post("/batch", json.dumps(batch_request))
            messages.append({
                "hostname": full_host_name,
                "message": f"Converted web forward to {rtype} record",
                "response": response
            })
            continue  # Move to the next rrset

        # Step 2: Check for an existing rrset of the desired type
        if rtype == "A":
            if check_for_a(domain_name, full_host_name, client):
                messages.append({
                    "hostname": full_host_name,
                    "message": f"{full_host_name} is already of type A with the desired configuration. Skipping."
                })
                continue
            elif check_for_cname(domain_name, full_host_name, client):
                # Delete CNAME before adding A record
                rrset_uri = f"/v1/zones/{domain_name}/rrsets/CNAME/{host if host else domain_name}"
                batch_request = [{"method": "DELETE", "uri": rrset_uri}]
        elif rtype == "CNAME":
            if check_for_cname(domain_name, full_host_name, client):
                messages.append({
                    "hostname": full_host_name,
                    "message": f"{full_host_name} is already of type CNAME with the desired configuration. Skipping."
                })
                continue
            elif check_for_a(domain_name, full_host_name, client):
                # Delete A record before adding CNAME
                rrset_uri = f"/v1/zones/{domain_name}/rrsets/A/{host if host else domain_name}"
                batch_request = [{"method": "DELETE", "uri": rrset_uri}]

        # Add the new rrset (A or CNAME)
        batch_request.append({
            "method": "POST",
            "uri": f"/v1/zones/{domain_name}/rrsets/{rtype}/{host if host else domain_name}",
            "body": {
                "ttl": ttl,
                "rdata": [rdata] if not isinstance(rdata, list) else rdata
            }
        })

        # Send the batch request for rrset creation
        response = client.post("/batch", json.dumps(batch_request))
        messages.append({
            "hostname": full_host_name,
            "message": f"Converted to {rtype} record",
            "response": response
        })

    # Process web forwards from YAML
    for web_forward in tqdm(domain_data["web_forwards"], desc=f"Iterating through web forwards in {domain_name}", leave=False):
        host = web_forward["host"]
        full_host_name = f"{domain_name}" if host is None else f"{host}.{domain_name}"
        redirect_to = web_forward["redirect_to"]
        forward_type = web_forward["forward_type"]

        # Check if a web forward already exists
        guid = get_webforward_guid(domain_name, full_host_name, client)
        if guid:
            messages.append({
                "hostname": full_host_name,
                "message": f"Web forward for {full_host_name} already exists with desired configuration. Skipping."
            })
            continue

        # Step 2: Check and delete any existing rrset before creating the web forward
        rrset_uri = None
        if check_for_a(domain_name, full_host_name, client):
            rrset_uri = f"/v1/zones/{domain_name}/rrsets/A/{host if host else domain_name}"
        elif check_for_cname(domain_name, full_host_name, client):
            rrset_uri = f"/v1/zones/{domain_name}/rrsets/CNAME/{host if host else domain_name}"

        # Prepare batch request
        batch_request = []
        if rrset_uri:
            batch_request.append({"method": "DELETE", "uri": rrset_uri})

        # Add the new web forward
        batch_request.append({
            "method": "POST",
            "uri": f"/v1/zones/{domain_name}/webforwards",
            "body": {
                "requestTo": full_host_name,
                "defaultRedirectTo": redirect_to,
                "defaultForwardType": forward_type
            }
        })

        # Send the batch request for web forward creation
        response = client.post("/batch", json.dumps(batch_request))
        messages.append({
            "hostname": full_host_name,
            "message": f"Converted rrset to web forward",
            "response": response
        })

# Final output of messages
print(json.dumps(messages, indent=2))