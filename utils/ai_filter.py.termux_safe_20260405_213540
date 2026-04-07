import os
import pickle

MODEL_PATHS = [
    os.path.expanduser("~/spamshield_test_final/spamshield_release/spam_model.pkl"),
    os.path.expanduser("~/spamshield/spam_model.pkl"),
]

_model = None
_vectorizer = None
_model_loaded = False
_model_error = None
_model_mode = "unknown"


def _load_model_once():
    global _model, _vectorizer, _model_loaded, _model_error, _model_mode

    if _model_loaded:
        return

    for path in MODEL_PATHS:
        if not os.path.exists(path):
            continue

        try:
            with open(path, "rb") as f:
                loaded = pickle.load(f)

            if isinstance(loaded, tuple) and len(loaded) == 2:
                _vectorizer, _model = loaded
                _model_mode = "tuple"
                _model_loaded = True
                _model_error = None
                return

            if isinstance(loaded, dict) and "vectorizer" in loaded and "model" in loaded:
                _vectorizer = loaded["vectorizer"]
                _model = loaded["model"]
                _model_mode = "dict"
                _model_loaded = True
                _model_error = None
                return

            # Sadece model varsa AI'yi kapat, sistem çökmesin
            if hasattr(loaded, "predict"):
                _model = None
                _vectorizer = None
                _model_mode = "model_only_without_vectorizer"
                _model_loaded = True
                _model_error = f"Model bulundu ama vectorizer yok: {type(loaded)}"
                return

            _model_error = f"Desteklenmeyen model tipi: {type(loaded)} | dosya: {path}"

        except Exception as e:
            _model_error = f"Model yükleme hatası: {e}"

    _model_loaded = True


def _normalize_prediction(pred):
    pred_str = str(pred).strip().lower()

    if pred_str in ["spam", "1", "true", "yes"]:
        return "SPAM"

    if pred_str in ["temiz", "clean", "ham", "0", "false", "no"]:
        return "TEMIZ"

    return "UNKNOWN"


def ai_analyze_message(message: str):
    _load_model_once()

    if _model is None or _vectorizer is None:
        return {
            "enabled": False,
            "result": "UNKNOWN",
            "score": 0,
            "error": _model_error or "AI devre dışı",
            "mode": _model_mode
        }

    try:
        text = (message or "").strip()
        X = _vectorizer.transform([text])
        pred = _model.predict(X)[0]
        result = _normalize_prediction(pred)

        if result == "SPAM":
            return {
                "enabled": True,
                "result": "SPAM",
                "score": 45,
                "error": None,
                "mode": _model_mode
            }

        if result == "TEMIZ":
            return {
                "enabled": True,
                "result": "TEMIZ",
                "score": 0,
                "error": None,
                "mode": _model_mode
            }

        return {
            "enabled": False,
            "result": "UNKNOWN",
            "score": 0,
            "error": f"Tanımsız prediction sonucu: {pred}",
            "mode": _model_mode
        }

    except Exception as e:
        return {
            "enabled": False,
            "result": "UNKNOWN",
            "score": 0,
            "error": f"AI analiz hatası: {e}",
            "mode": _model_mode
        }
