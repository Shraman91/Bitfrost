import os
import json
import logging
from typing import Any, Dict, List, Optional
from backend.config.settings import settings

logger = logging.getLogger("agentarena.db")

DB_CACHE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".arena_db.json"))


class InMemoryDocumentSnapshot:
    def __init__(self, doc_id: str, data: Optional[Dict[str, Any]]):
        self.id = doc_id
        self._data = data

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self) -> Optional[Dict[str, Any]]:
        return dict(self._data) if self._data is not None else None


class InMemoryDocumentReference:
    def __init__(self, collection: "InMemoryCollectionReference", doc_id: str):
        self.collection = collection
        self.id = doc_id

    def get(self) -> InMemoryDocumentSnapshot:
        data = self.collection.store.get(self.id)
        return InMemoryDocumentSnapshot(self.id, data)

    def set(self, data: Dict[str, Any], merge: bool = False) -> None:
        if merge and self.id in self.collection.store:
            existing = self.collection.store[self.id]
            merged = {**existing, **data}
            self.collection.store[self.id] = merged
        else:
            self.collection.store[self.id] = dict(data)
        self.collection.client._save_to_disk()

    def update(self, data: Dict[str, Any]) -> None:
        if self.id not in self.collection.store:
            raise KeyError(f"Document {self.id} does not exist.")
        doc = self.collection.store[self.id]
        for k, v in data.items():
            if "." in k:
                parts = k.split(".")
                curr = doc
                for part in parts[:-1]:
                    if part not in curr or not isinstance(curr[part], dict):
                        curr[part] = {}
                    curr = curr[part]
                curr[parts[-1]] = v
            else:
                doc[k] = v
        self.collection.store[self.id] = doc
        self.collection.client._save_to_disk()

    def delete(self) -> None:
        self.collection.store.pop(self.id, None)
        self.collection.client._save_to_disk()


class InMemoryQuery:
    def __init__(self, collection: "InMemoryCollectionReference"):
        self.collection = collection
        self.filters = []
        self._order_by = None
        self._descending = False
        self._limit = None

    def where(self, field: str, op: str, value: Any) -> "InMemoryQuery":
        new_q = InMemoryQuery(self.collection)
        new_q.filters = list(self.filters)
        new_q.filters.append((field, op, value))
        new_q._order_by = self._order_by
        new_q._descending = self._descending
        new_q._limit = self._limit
        return new_q

    def order_by(self, field: str, direction: str = "ASCENDING") -> "InMemoryQuery":
        self._order_by = field
        self._descending = direction.upper() in ("DESCENDING", "DESC")
        return self

    def limit(self, count: int) -> "InMemoryQuery":
        self._limit = count
        return self

    def stream(self) -> List[InMemoryDocumentSnapshot]:
        results = []
        for doc_id, data in self.collection.store.items():
            match = True
            for field, op, val in self.filters:
                item_val = data.get(field)
                if op == "==" and item_val != val:
                    match = False
                    break
                elif op == "!=" and item_val == val:
                    match = False
                    break
                elif op == "in" and item_val not in val:
                    match = False
                    break
            if match:
                results.append(InMemoryDocumentSnapshot(doc_id, data))

        if self._order_by:
            results.sort(
                key=lambda doc: doc.to_dict().get(self._order_by, ""),
                reverse=self._descending
            )

        if self._limit is not None:
            results = results[:self._limit]

        return results


class InMemoryCollectionReference:
    def __init__(self, name: str, client: "InMemoryFirestoreClient"):
        self.name = name
        self.client = client
        if name not in self.client._stores:
            self.client._stores[name] = {}
        self.store = self.client._stores[name]

    def document(self, doc_id: str) -> InMemoryDocumentReference:
        return InMemoryDocumentReference(self, doc_id)

    def stream(self) -> List[InMemoryDocumentSnapshot]:
        return [InMemoryDocumentSnapshot(k, v) for k, v in self.store.items()]

    def where(self, field: str, op: str, value: Any) -> InMemoryQuery:
        q = InMemoryQuery(self)
        return q.where(field, op, value)


class InMemoryFirestoreClient:
    def __init__(self):
        self._stores: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._load_from_disk()

    def _load_from_disk(self):
        if os.path.exists(DB_CACHE_FILE):
            try:
                with open(DB_CACHE_FILE, "r", encoding="utf-8") as f:
                    self._stores = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load .arena_db.json: {e}")

    def _save_to_disk(self):
        try:
            with open(DB_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self._stores, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to write .arena_db.json: {e}")

    def collection(self, name: str) -> InMemoryCollectionReference:
        return InMemoryCollectionReference(name, self)


# Global client instance
db_client = None


def get_db():
    global db_client
    if db_client is not None:
        return db_client

    # Check if Firestore credentials are provided
    has_credentials = (
        bool(settings.firebase_service_account_json) or
        (bool(settings.firebase_service_account_path) and os.path.exists(settings.firebase_service_account_path)) or
        (bool(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")) and os.path.exists(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")))
    )

    if has_credentials:
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore

            if settings.firebase_service_account_json:
                cert_dict = json.loads(settings.firebase_service_account_json)
                cred = credentials.Certificate(cert_dict)
                firebase_admin.initialize_app(cred, {"projectId": settings.firebase_project_id})
                db_client = firestore.client()
                logger.info("Initialized Firebase Firestore with JSON credentials.")
                return db_client

            if settings.firebase_service_account_path and os.path.exists(settings.firebase_service_account_path):
                cred = credentials.Certificate(settings.firebase_service_account_path)
                firebase_admin.initialize_app(cred, {"projectId": settings.firebase_project_id})
                db_client = firestore.client()
                logger.info(f"Initialized Firebase Firestore with service account file {settings.firebase_service_account_path}.")
                return db_client

            if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and os.path.exists(os.environ["GOOGLE_APPLICATION_CREDENTIALS"]):
                firebase_admin.initialize_app(options={"projectId": settings.firebase_project_id})
                db_client = firestore.client()
                logger.info("Initialized Firebase Firestore with GOOGLE_APPLICATION_CREDENTIALS.")
                return db_client

        except ImportError:
            logger.info("firebase-admin package not installed. Using local persistence fallback.")
        except Exception as e:
            logger.warning(f"Failed to initialize Firestore with credentials: {e}. Falling back to local storage.")

    # Fallback to local persisted in-memory Firestore client
    db_client = InMemoryFirestoreClient()
    return db_client
