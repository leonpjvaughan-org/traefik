# Traefik with Docker (swarm mode) and Let's Encrypt (using Cloudflare DNS challenge)

## Setup Summary

See [Setup (long-version)](#setup-long-version) for more details including pre-requisites.

1. `docker swarm init`
2. `docker network create --driver=overlay traefik-internal-network`
3. `docker secret create cloudflare_api_token ./secrets/cloudflare_api_token.txt`
4. Export the `TRAEFIK_URL_BASE` and `ACME_EMAIL` environment variables.
5. `docker stack deploy -c docker-compose.yml traefik`

Options to be able to reach your traefik instance:

1. Create a DNS A record for `*.<your-domain>` pointing to your server's IP address.
2. Or for local development, add a line to your `/etc/hosts` file (Linux/Mac) or `C:\Windows\System32\drivers\etc\hosts` file (Windows) like this:

    ```txt
    127.0.0.1 traefik.<your-domain>
    ```

Note: `TRAEFIK_URL_BASE` should be set to your domain name, e.g. `example.com`.

### All in one

```shell
docker swarm init
docker network create --driver=overlay traefik-internal-network
docker secret create cloudflare_api_token ./secrets/cloudflare_api_token.txt
export TRAEFIK_URL_BASE=yourdomain.com
export ACME_EMAIL=youremail@example.com
docker stack deploy -c docker-compose.yml traefik
```

## Setup (long-version)

Prerequisites:

1. A domain name. Most domain regristrars allow you to change nameservers after purchase.
2. A Cloudflare account. Sign up at <https://www.cloudflare.com/>.
3. [Onboard your domain to Cloudflare](https://developers.cloudflare.com/fundamentals/manage-domains/add-site/). This involves changing your domain's nameservers to those provided by Cloudflare.
4. Point your domain's nameservers to Cloudflare's nameservers. This is done at your domain registrar.

5. Create a [Cloudflare API token](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/) with the following permissions:
   - Zone: DNS: Edit
   - Zone: Zone: Read
   - Account: Account Settings: Read
   - Account: Members: Read
   - Include all zones in account (or specify the relevant zone)

6. Save the API token to a file named `cloudflare_api_token.txt` in the `secrets` directory.

Then follow the steps in the [Setup Summary](#setup-summary) section above.

### Other providers

To configure tokens for other DNS providers, see the documentation for:

[lego](https://go-acme.github.io/lego/dns/cloudflare/)

## Checks

### Check Traefik Logs

```shell
docker service logs traefik_traefik --follow
```

### Check Certificates

open the acme.json file to see the certificates:

```json
{
  "acme-cf": {
    "Account": {
      "Email": "xxx",
      "Registration": {
        "body": {
          "status": "valid"
        },
        "uri": "https://acme-staging-v02.api.letsencrypt.org/acme/acct/[REDACTED]"
      },
      "PrivateKey": "[REDACTED_4096_BIT_RSA_KEY]",
      "KeyType": "4096"
    },
    "Certificates": [
      {
        "domain": {
          "main": "*.staging.${TRAEFIK_URL_BASE}",
          "sans": ["staging.${TRAEFIK_URL_BASE}"]
        },
        "certificate": "[REDACTED_CERTIFICATE_CHAIN]",
        "key": "[REDACTED_PRIVATE_KEY]",
        "Store": "default"
      },
      {
        "domain": {
          "main": "*.prod.${TRAEFIK_URL_BASE}",
          "sans": ["prod.${TRAEFIK_URL_BASE}"]
        },
        "certificate": "[REDACTED_CERTIFICATE_CHAIN]",
        "key": "[REDACTED_PRIVATE_KEY]",
        "Store": "default"
      },
      {
        "domain": {
          "main": "*.localhost.${TRAEFIK_URL_BASE}",
          "sans": ["localhost.${TRAEFIK_URL_BASE}"]
        },
        "certificate": "[REDACTED_CERTIFICATE_CHAIN]",
        "key": "[REDACTED_PRIVATE_KEY]",
        "Store": "default"
      }
    ]
  }
}
```

### Run the test stack

```shell
docker stack deploy -c docker-compose.test.yml httpbin-test
```

Then access the test service at:

- `http://httpbin.staging.your-domain` (with staging certificate)
- `http://httpbin.prod.your-domain` (with production certificate)
