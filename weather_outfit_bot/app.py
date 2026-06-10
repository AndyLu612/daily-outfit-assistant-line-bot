from flask import Flask, abort, jsonify, request

from .advice import build_reply, detect_intent, extract_city, normalize_intent
from .config import Config
from .firebase_store import FirestoreStore
from .gemini_client import GeminiClient
from .line_api import LineApi
from .weather_api import WeatherApi


def create_app() -> Flask:
    app = Flask(__name__)
    weather_api = WeatherApi(Config.cwa_api_key)
    store = FirestoreStore()
    line_api = LineApi(Config.line_channel_access_token, Config.line_channel_secret)
    gemini = GeminiClient(Config.gemini_api_key, Config.gemini_model)

    def normalize_dialogflow_city(value) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            return value.get("city") or value.get("admin-area") or value.get("subadmin-area") or ""
        if isinstance(value, list) and value:
            return normalize_dialogflow_city(value[0])
        return ""

    def handle_text(text: str, user_id: str = "", city_hint: str = "", intent_hint: str = "") -> dict:
        saved_city = store.get_user_city(user_id) if user_id else None
        city = city_hint or extract_city(text, saved_city or Config.default_city)
        intent = normalize_intent(intent_hint, text) if intent_hint else detect_intent(text)
        weather = weather_api.get_forecast(city)
        rule_reply = build_reply(intent, weather, text)
        reply, used_gemini = gemini.improve_reply(text, intent, weather, rule_reply)

        try:
            if user_id:
                store.save_user_city(user_id, city)
            store.save_query_log(user_id, intent, city, text)
        except Exception as error:
            print(f"Firestore write failed: {error}", flush=True)

        return {
            "intent": intent,
            "city": city,
            "reply": reply,
            "firebaseEnabled": store.enabled,
            "weatherApiEnabled": bool(Config.cwa_api_key),
            "geminiEnabled": gemini.enabled,
            "geminiUsed": used_gemini,
            "replySource": "gemini" if used_gemini else "rules",
        }

    @app.get("/")
    def index():
        return jsonify(
            {
                "name": "今日穿搭小幫手 Line Bot",
                "demo": "/demo?text=今天台中要帶傘嗎",
                "firebaseEnabled": store.enabled,
                "weatherApiEnabled": bool(Config.cwa_api_key),
                "geminiEnabled": gemini.enabled,
            }
        )

    @app.get("/health")
    def health():
        return jsonify(
            {
                "status": "ok",
                "dialogflowWebhook": "/dialogflow",
                "lineWebhookOptional": "/callback",
                "lineAccessTokenConfigured": bool(Config.line_channel_access_token),
                "lineSecretConfigured": bool(Config.line_channel_secret),
                "cwaApiKeyConfigured": bool(Config.cwa_api_key),
                "geminiApiKeyConfigured": bool(Config.gemini_api_key),
                "geminiModel": Config.gemini_model,
                "firebaseEnabled": store.enabled,
                "defaultCity": Config.default_city,
            }
        )

    @app.get("/demo")
    def demo():
        text = request.args.get("text", "今天台中穿什麼")
        city = request.args.get("city")
        if city and city not in text:
            text = f"{text} {city}"
        return jsonify(handle_text(text, user_id="demo-user"))

    @app.post("/callback")
    def callback():
        if line_api.enabled and not line_api.verify_signature(request.get_data(), request.headers.get("X-Line-Signature", "")):
            abort(403)

        payload = request.get_json(silent=True) or {}
        events = payload.get("events", [])
        for event in events:
            if event.get("type") != "message":
                continue
            message = event.get("message", {})
            if message.get("type") != "text":
                continue
            user_id = event.get("source", {}).get("userId", "")
            try:
                result = handle_text(message.get("text", ""), user_id=user_id)
                line_api.reply_text(event.get("replyToken", ""), result["reply"])
            except Exception as error:
                print(f"LINE callback error: {error}", flush=True)
        return "OK"

    @app.post("/dialogflow")
    def dialogflow():
        payload = request.get_json(silent=True) or {}
        query_result = payload.get("queryResult", {})
        text = query_result.get("queryText", "")
        parameters = query_result.get("parameters", {})
        intent_hint = query_result.get("intent", {}).get("displayName", "")
        city_hint = normalize_dialogflow_city(parameters.get("city") or parameters.get("geo-city"))
        original_payload = payload.get("originalDetectIntentRequest", {}).get("payload", {})
        user_id = original_payload.get("data", {}).get("source", {}).get("userId", "dialogflow-user")

        result = handle_text(text, user_id=user_id, city_hint=city_hint, intent_hint=intent_hint)
        return jsonify({"fulfillmentText": result["reply"]})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
