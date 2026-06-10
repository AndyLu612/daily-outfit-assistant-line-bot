import json
import urllib.parse
import urllib.request

from .advice import WeatherInfo


class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def improve_reply(self, user_text: str, intent: str, weather: WeatherInfo, rule_reply: str) -> tuple[str, bool]:
        if not self.enabled:
            return rule_reply, False

        prompt = f"""
你是「今日穿搭小幫手」Line Bot。請根據天氣資料，用繁體中文回覆使用者。

規則：
- 回覆 2 到 3 行，適合 LINE 訊息。
- 不要編造天氣資料，只能使用我提供的天氣、溫度、降雨機率。
- 如果使用者問穿搭，要直接回答穿長袖/短袖/外套是否適合。
- 如果使用者問帶傘，要明確說要不要帶傘。
- 如果使用者問雨衣、雨具或騎車，要回答要不要帶雨衣，並提醒騎車雨衣比雨傘安全。
- 如果使用者問曬衣服，要回答適不適合曬、建議曬室內或戶外。
- 不要照抄原本規則回覆；請改寫成更像真人助理的生活化建議。
- 可以用「建議」「比較保險」「不太適合」這類自然語氣。
- 不要使用 Markdown，不要條列。

使用者問題：{user_text}
判斷類型：{intent}
城市：{weather.city}
天氣：{weather.weather}
最低溫：{weather.min_temp}
最高溫：{weather.max_temp}
降雨機率：{weather.rain_probability}%
原本規則回覆：
{rule_reply}
""".strip()

        body = json.dumps(
            {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.4,
                    "maxOutputTokens": 180,
                },
            }
        ).encode("utf-8")
        query = urllib.parse.urlencode({"key": self.api_key})
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?{query}"
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
            parts = payload["candidates"][0]["content"]["parts"]
            text = "".join(part.get("text", "") for part in parts).strip()
            return (text, True) if text else (rule_reply, False)
        except Exception as error:
            print(f"Gemini request failed: {error}", flush=True)
            return rule_reply, False
