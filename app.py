from flask import Flask, request, Response
import requests
import tyro
from loguru import logger
import sys
import os

app = Flask("Webhook Distributor")

hosts: list[str] = []


@app.route(
    "/", defaults={"path": ""}, methods=["GET", "POST"]
)  # ref. https://medium.com/@zwork101/making-a-flask-proxy-server-online-in-10-lines-of-code-44b8721bca6
@app.route("/<path>", methods=["GET", "POST"])
def redirect_to_API_HOST(
    path: str,
) -> (
    Response
):  # NOTE var :path will be unused as all path we need will be read from :request i.e. from flask import request
    logger.info("Incoming {} request from {}", request.method, request.remote_addr)
    responses = {}
    for host in hosts:
        try:
            res = requests.request(  # ref. https://stackoverflow.com/a/36601467/248616
                method=request.method,
                url=host,
                headers={
                    k: v for k, v in request.headers if k.lower() != "host"
                },  # exclude 'host' header
                data=request.get_data(),
            )

            # https://stackoverflow.com/questions/8265583/dividing-python-module-into-multiple-regions
            # region exclude some keys in :res response
            excluded_headers = [
                "content-encoding",
                "content-length",
                "transfer-encoding",
                "connection",
            ]  # NOTE we here exclude all "hop-by-hop headers" defined by RFC 2616 section 13.5.1 ref. https://www.rfc-editor.org/rfc/rfc2616#section-13.5.1
            headers = [
                (k, v)
                for k, v in res.raw.headers.items()
                if k.lower() not in excluded_headers
            ]
            # endregion exclude some keys in :res response

            logger.info("{} -> {} {}", host, res.status_code, res.reason)
            responses[host] = res.status_code
        except Exception as e:
            logger.error("Failed to forward to {}: {}", host, e)
            responses[host] = 502

    # response = Response(responses, res.status_code, headers)

    # TypeError: Object of type Response is not JSON serializable
    # return a normal Discord response otherwise DiscordWebhook will got wrong
    return responses


def main(
    host: str = "0.0.0.0",
    port: int = 3128,
    webhooks: tuple[str, ...] = (),
    log_file: str = "webhook-distributor.log",
) -> None:
    global hosts

    # Configure loguru
    logger.remove()  # remove default stderr handler
    logger.add(sys.stderr, level="INFO")
    if log_file:
        logger.add(log_file, rotation="10 MB", retention="7 days", level="DEBUG")

    # Resolve webhook URLs
    if webhooks:
        hosts = list(webhooks)
        logger.info("Using {} webhook URL(s) from CLI arguments", len(hosts))
    else:
        webhooks_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "webhooks.txt")
        if os.path.exists(webhooks_file):
            with open(webhooks_file, "r") as fp:
                hosts = [line.strip() for line in fp.readlines() if line.strip()]
            if not hosts:
                logger.error("webhooks.txt is empty — no destinations configured")
                sys.exit(1)
            logger.info("Loaded {} webhook URL(s) from webhooks.txt", len(hosts))
        else:
            logger.warning("webhooks.txt not found and no --webhooks provided — no destinations configured")
            logger.warning("Use --webhooks URL1 URL2 ... or create webhooks.txt")
            sys.exit(1)

    logger.info("Starting Webhook Distributor on {}:{}", host, port)
    for i, h in enumerate(hosts, 1):
        logger.info("  Destination {}: {}", i, h)

    app.run(host=host, port=port)


if __name__ == "__main__":
    tyro.cli(main)
