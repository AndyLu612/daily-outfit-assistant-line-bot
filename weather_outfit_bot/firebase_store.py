from datetime import datetime, timezone


class FirestoreStore:
    def __init__(self):
        self.db = None
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore

            if not firebase_admin._apps:
                firebase_admin.initialize_app()
            self.db = firestore.client()
        except Exception:
            self.db = None

    @property
    def enabled(self) -> bool:
        return self.db is not None

    def get_user_city(self, user_id: str) -> str | None:
        if not self.enabled or not user_id:
            return None
        doc = self.db.collection("users").document(user_id).get()
        if not doc.exists:
            return None
        return doc.to_dict().get("city")

    def save_user_city(self, user_id: str, city: str) -> None:
        if not self.enabled or not user_id:
            return
        self.db.collection("users").document(user_id).set(
            {
                "city": city,
                "updatedAt": datetime.now(timezone.utc),
            },
            merge=True,
        )

    def save_query_log(self, user_id: str, intent: str, city: str, text: str) -> None:
        if not self.enabled:
            return
        self.db.collection("queryLogs").add(
            {
                "userId": user_id or "demo",
                "intent": intent,
                "city": city,
                "text": text,
                "createdAt": datetime.now(timezone.utc),
            }
        )
