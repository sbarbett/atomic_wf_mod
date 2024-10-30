atomic_wf_mod
======================

## Overview

`atomic_wf_mod` is a tool designed to modify UltraDNS web forwards into DNS resource records (A and CNAME), and vice-versa, in an atomic manner. By leveraging the UDNS REST API, this tool performs batch requests to delete existing records and create new ones, ensuring seamless transitions without intermediate states that could lead to unwanted NXDOMAIN caching.

This script supports:

* Converting existing DNS records (A/CNAME) to web forwards.
* Converting web forwards to DNS records (A/CNAME).
* Configuring actions for multiple domains and hosts through a single YAML file.

## Dependencies

To install the required Python dependencies, use `requirements.txt`:

```bash
pip install -r requirements.txt
```

The dependencies include:

* `pyyaml`: For handling YAML configuration files.
* `ultra_rest_client`: For interfacing with the UDNS API.

## YAML Config

The script uses a YAML file to specify actions for each domain and host. By default, it will look for `config.yml` in the current working directory, but a custom file can be specified using the `--yaml` or `-y` argument.

An example file can be found under `config-example.yml`.

### YAML Parameters

Credentials need to be specified once at the start of the file.

* `username`: Your UltraDNS username.
* `password`: Your UltraDNS password.

Each domain can contain multiple hosts. For each host under a domain:

* **For Web Forwards:**
	- `redirect_to`: The target URL for the web forward.
	- `forward_type`: HTTP redirect type (e.g., `HTTP_301_REDIRECT`, `HTTP_302_REDIRECT`).
* **For DNS Records:**
	- `rtype`: The record type (e.g., A, CNAME).
	- `rdata`: The record data (e.g., IP address for A records or a domain for CNAME records).
	- `ttl`: The TTL (time-to-live) for the DNS record.

## Usage

Clone the repository.

```bash
git clone https://github.com/sbarbett/atomic_wf_mod
cd atomic_wf_mod
```

To run the script, use the following command:

```bash
python3 src/atomic.py
```

...or:

```bash
chmod +x src/atomic.py
./src/atomic.py
```

### Optional Arguments

* **Specify a custom YAML file:** Use the `--yaml` or `-y` argument to specify a custom YAML file path:

	```bash
	python3 atomic.py --yaml /path/to/your/custom_config.yml
	```

* **Display help:** Use the `--help` or `-h` argument to display usage information:

	```bash
	python3 atomic.py --help
	```