#!/usr/bin/env python3

import yaml
import json
import argparse
from ultra_rest_client.connection import RestApiConnection

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

username = config["username"]
password = config["password"]

# Initialize UltraDNS client
client = RestApiConnection(host='api.ultradns.com')
client.auth(username, password)

# Iterate over domains and hosts
for domain_name, hosts in config.items():
    if domain_name in ["username", "password"]:
        continue  # Skip credentials in config

    for host_name, params in hosts.items():
        # Determine the full host name
        full_host_name = f"{domain_name}." if host_name == "@" else f"{host_name}.{domain_name}"

        # Check if transitioning to a web forward
        if "redirect_to" in params and "forward_type" in params:
            redirect_to = params["redirect_to"]
            forward_type = params["forward_type"]
            
            # Check if an A record exists
            existing_rrset = client.get(f"/v3/zones/{domain_name}/rrsets/A")
            rrset_uri = None
            
            # Handle response type
            if isinstance(existing_rrset, dict) and "rrSets" in existing_rrset:
                for rrset in existing_rrset["rrSets"]:
                    # Compare ownerName directly with full_host_name for non-apex
                    if rrset["ownerName"].rstrip(".") == full_host_name.rstrip("."):
                        rrset_uri = f"/v1/zones/{domain_name}/rrsets/A/{host_name if host_name != '@' else domain_name}"
                        break
            
            # If no A record, check for CNAME
            if not rrset_uri:
                existing_rrset = client.get(f"/v3/zones/{domain_name}/rrsets/CNAME")
                
                if isinstance(existing_rrset, dict) and "rrSets" in existing_rrset:
                    for rrset in existing_rrset["rrSets"]:
                        if rrset["ownerName"].rstrip(".") == full_host_name.rstrip("."):
                            rrset_uri = f"/v1/zones/{domain_name}/rrsets/CNAME/{host_name if host_name != '@' else domain_name}"
                            break
            
            # Output error message if no A or CNAME record exists
            if rrset_uri is None:
                print(f"No CNAME or A record exists for {full_host_name}, skipping batch request.")
                continue
            
            # Create batch request with DELETE and POST actions
            batch_request = [
                {"method": "DELETE", "uri": rrset_uri},
                {
                    "method": "POST",
                    "uri": f"/v1/zones/{domain_name}/webforwards",
                    "body": {
                        "requestTo": full_host_name,
                        "defaultRedirectTo": redirect_to,
                        "defaultForwardType": forward_type
                    }
                }
            ]
            
            # Send batch request
            response = client.post("/batch", json.dumps(batch_request))
            print(response)

        # Check if creating an rrset (deleting a web forward)
        elif "rdata" in params and "rtype" in params and "ttl" in params:
            rtype = params["rtype"]
            rdata = params["rdata"]
            ttl = params["ttl"]
            
            # Ensure rdata is a list
            if not isinstance(rdata, list):
                rdata = [rdata]
            
            # Check for an existing web forward
            existing_forwards = client.get(f"/v3/zones/{domain_name}/webforwards")
            if isinstance(existing_forwards, list) and existing_forwards[0].get("errorCode") == 70002:
                print(f"No web forwards exist for {full_host_name}.")
                continue
            elif not isinstance(existing_forwards, dict) or "webForwards" not in existing_forwards:
                print(f"Unexpected response structure for web forwards request: {existing_forwards}")
                continue
            
            guid = None
            for forward in existing_forwards["webForwards"]:
                # Compare requestTo, accounting for potential missing trailing dot
                if forward["requestTo"].rstrip(".") == full_host_name.rstrip("."):
                    guid = forward["guid"]
                    break
            
            # Output error message if no web forward exists
            if guid is None:
                print(f"No web forward exists for {host_name}.{domain_name}, skipping batch request.")
                continue
            
            # Create batch request with DELETE and POST actions
            batch_request = [
                {"method": "DELETE", "uri": f"/v3/zones/{domain_name}/webforwards/{guid}"},
                {
                    "method": "POST",
                    "uri": f"/v1/zones/{domain_name}/rrsets/{rtype}/{host_name if host_name != '@' else domain_name}",
                    "body": {
                        "ttl": ttl,
                        "rdata": rdata  # rdata is now ensured to be a list
                    }
                }
            ]
            
            # Send batch request
            response = client.post("/batch", json.dumps(batch_request))
            print(response)

        # Handle case where required parameters are missing
        else:
            print(f"Missing parameters for {host_name}.{domain_name}. Check config-example.yml for details.")
