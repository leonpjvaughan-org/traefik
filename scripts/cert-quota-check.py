#!/usr/bin/env python3
import sys
import json

try:
    import requests
except ImportError:
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests
from datetime import datetime, timedelta, timezone
from collections import Counter
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Check Let's Encrypt certificate rate limits for a domain"
    )
    parser.add_argument("domain", help="Domain to check")
    args = parser.parse_args()

    domain = args.domain

    # Get timestamp from 7 days ago in ISO format
    week_ago = (datetime.now(tz=timezone.utc) - timedelta(days=7)).strftime(
        "%Y-%m-%dT%H:%M:%S"
    )

    # Get certificates issued in last 7 days
    url = f"https://crt.sh/?q={domain}&output=json&exclude=expired"

    try:
        print("Fetching certificates from crt.sh...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        if not response.text.strip():
            print("No certificates found or error fetching data.")
            sys.exit(1)

        all_certs = response.json()
        print("Fetched certificates from crt.sh")

    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        sys.exit(1)

    # Filter for Let's Encrypt certificates from last 7 days
    letsencrypt_certs = []
    for cert in all_certs:
        if "Let's Encrypt" in cert.get("issuer_name", ""):
            if cert.get("not_before", "") >= week_ago:
                letsencrypt_certs.append(cert)

    # Deduplicate by serial number
    seen_serials = set()
    recent_certs = []
    for cert in letsencrypt_certs:
        serial = cert.get("serial_number", "")
        if serial and serial not in seen_serials:
            seen_serials.add(serial)
            recent_certs.append(cert)

    print("\n=== LET'S ENCRYPT RATE LIMIT CHECK ===")

    # QUOTA 1: New Certificates per Registered Domain (50/week)
    cert_count = len(recent_certs)
    print(f"Certificates issued in last 7 days: {cert_count}/50")
    print(f"   Remaining quota: {50 - cert_count}")
    if cert_count > 40:
        print("   WARNING: Approaching rate limit!")
    print()

    # QUOTA 2: New Certificates per Exact Set of Identifiers (5/week)
    print("Exact identifier sets (5 certificates max per set):")

    # Group certificates by their exact set of identifiers
    identifier_sets = []
    for cert in recent_certs:
        name_value = cert.get("name_value", "")
        if name_value:
            # Split by newlines, sort, and join back
            domains = sorted(name_value.split("\n"))
            identifier_set = ",".join(domains)
            identifier_sets.append(identifier_set)

    # Count occurrences of each identifier set
    set_counts = Counter(identifier_sets)

    for identifier_set, count in set_counts.items():
        if count > 3:
            print(f"   WARNING: {count}/5: {identifier_set}")
        else:
            print(f"   {count}/5: {identifier_set}")
    print()

    # QUOTA 3: New Orders per Account (300/3hours) - Not trackable via crt.sh
    print("New Orders per Account (300/3hours): Not trackable via public logs")
    print("   This limit is per ACME account, not visible in certificate transparency")
    print()

    print("Done.")


if __name__ == "__main__":
    main()
