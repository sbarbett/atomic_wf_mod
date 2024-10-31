# Helper Functions
def check_for_a(domain, hostname, c):
    """Check if an A record exists for a given hostname in the specified domain."""
    existing_rrset = c.get(f"/v3/zones/{domain}/rrsets/A")
    if isinstance(existing_rrset, dict) and "rrSets" in existing_rrset:
        for record in existing_rrset["rrSets"]:
            if record["ownerName"].rstrip(".") == hostname.rstrip("."):
                return True
    return False


def check_for_cname(domain, hostname, c):
    """Check if a CNAME record exists for a given hostname in the specified domain."""
    existing_rrset = c.get(f"/v3/zones/{domain}/rrsets/CNAME")
    if isinstance(existing_rrset, dict) and "rrSets" in existing_rrset:
        for record in existing_rrset["rrSets"]:
            if record["ownerName"].rstrip(".") == hostname.rstrip("."):
                return True
    return False


def get_webforward_guid(domain, hostname, c):
    """Get the GUID of a web forward if it exists for a given hostname in the specified domain."""
    existing_forwards = c.get(f"/v3/zones/{domain}/webforwards")
    if isinstance(existing_forwards, dict) and "webForwards" in existing_forwards:
        for forward in existing_forwards["webForwards"]:
            if forward["requestTo"].rstrip(".") == hostname.rstrip("."):
                return forward["guid"]
    return None