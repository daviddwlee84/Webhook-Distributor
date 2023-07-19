from flask import Flask, request, Response
import requests

app = Flask("Webhook Distributor")

with open("webhooks.txt", "r") as fp:
    hosts = [line.strip() for line in fp.readlines()]

assert hosts, "Must at least have one host."


@app.route(
    "/", defaults={"path": ""}, methods=["GET", "POST"]
)  # ref. https://medium.com/@zwork101/making-a-flask-proxy-server-online-in-10-lines-of-code-44b8721bca6
@app.route("/<path>", methods=["GET", "POST"])
def redirect_to_API_HOST(
    path: str,
) -> (
    Response
):  # NOTE var :path will be unused as all path we need will be read from :request i.e. from flask import request
    responses = {}
    for host in hosts:
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

        print(host, res, res.content)
        responses[host] = res.status_code

    # response = Response(responses, res.status_code, headers)

    # TypeError: Object of type Response is not JSON serializable
    # return a normal Discord response otherwise DiscordWebhook will got wrong
    return responses


if __name__ == "__main__":
    # TODO: remove hardcoded port
    # app.run(host="0.0.0.0", port=3128, ssl_context="adhoc")
    app.run(host="0.0.0.0", port=3128)
