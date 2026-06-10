import json
import base64
import hashlib
import hmac
import urllib.request


class LineApi:
    def __init__(self, channel_access_token: str, channel_secret: str = ""):
        self.channel_access_token = channel_access_token
        self.channel_secret = channel_secret

    @property
    def enabled(self) -> bool:
        return bool(self.channel_access_token)

    def verify_signature(self, body: bytes, signature: str) -> bool:
        if not self.channel_secret:
            return True
        digest = hmac.new(self.channel_secret.encode("utf-8"), body, hashlib.sha256).digest()
        expected = base64.b64encode(digest).decode("utf-8")
        return hmac.compare_digest(expected, signature)

    def reply_text(self, reply_token: str, text: str) -> None:
        if not self.enabled or not reply_token:
            return

        body = json.dumps(
            {
                "replyToken": reply_token,
                "messages": [{"type": "text", "text": text}],
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            "https://api.line.me/v2/bot/message/reply",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.channel_access_token}",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=10):
            return
