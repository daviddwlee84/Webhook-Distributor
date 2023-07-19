from discord_webhook import DiscordWebhook

webhook = DiscordWebhook(url="http://127.0.0.1:3128", content="test", tts=False)
webhook.execute()
