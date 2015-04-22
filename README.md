atomic_wf_mod
======================

The UltraDNS UI lacks functionality for replacing resource record sets with web forwards in a fashion that doesn't involve deleting and creating a new entry. To eliminate the risk of null cashing, this script will delete and add the new record in a single batch request through the REST API. Usage:

```
atomic_wf_mod.sh url username password zone_name host_name request_to redirect_to forward_type
```