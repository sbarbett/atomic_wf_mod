# YAML Parser
def parse_yaml(config, tqdm):
    parsed_domains = []

    for domain_name, hosts in tqdm(config.items(), desc="Parsing items from YAML"):
        # Skip credentials in the YAML
        if domain_name in ["username", "password"]:
            continue

        # Add a trailing dot to the domain if it's missing
        domain_name = domain_name if domain_name.endswith('.') else domain_name + '.'

        # Initialize lists for rrsets and web forwards
        rrsets = []
        web_forwards = []

        for host_name, params in tqdm(hosts.items(), desc=f"Processing hosts from {domain_name} YAML", leave=False):
            # Check if it's an rrset
            if "rdata" in params and "rtype" in params and "ttl" in params:
                # Validate apex record and exclude unsupported CNAMEs
                if host_name == "@" and params["rtype"].upper() == "CNAME":
                    print(f"Warning: CNAME records cannot be apex records. Skipping {host_name}.{domain_name}")
                    continue

                rrsets.append({
                    "host": None if host_name == "@" else host_name,
                    "rdata": params["rdata"],
                    "rtype": params["rtype"],
                    "ttl": params["ttl"]
                })

            # Check if it's a web forward
            elif "redirect_to" in params and "forward_type" in params:
                web_forwards.append({
                    "host": None if host_name == "@" else host_name,
                    "redirect_to": params["redirect_to"],
                    "forward_type": params["forward_type"]
                })

            else:
                print(f"Warning: Missing parameters for {host_name}.{domain_name}. Check config-example.yml for details.")

        # Append the domain entry to the parsed list
        parsed_domains.append({
            "domain": domain_name,
            "rrsets": rrsets,
            "web_forwards": web_forwards
        })

    return parsed_domains

