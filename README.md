# Webhook Distributor

Can be used as sort of a proxy that can pass a webhook to multiple webhook hosts
Receive HTTP request and call HTTPS servers like Discord Webhook

## Getting Started

1. Add Discord webhooks to `webhooks.txt` 
2. Install dependencies `pip install -r requirements.txt`
3. Start server `python app.py`
4. (optional) test with `python debug.py` in a separate terminal

## Note

- [python - Proxying to another web service with Flask - Stack Overflow](https://stackoverflow.com/questions/6656363/proxying-to-another-web-service-with-flask)

## Trouble Shooting

- [angular5 - Problems with flask and bad request - Stack Overflow](https://stackoverflow.com/questions/49389535/problems-with-flask-and-bad-request)
  - HTTPS issue
