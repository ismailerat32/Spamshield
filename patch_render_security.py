from pathlib import Path
import re

p = Path("app.py")
text = p.read_text(encoding="utf-8")

if "import os" not in text:
    text = "import os\n" + text

text = re.sub(
    r'app\s*=\s*Flask\(__name__\)',
    '''app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-change-this-now")
app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "0") == "1"

def apply_runtime_env_overrides():
    import json
    users_file = globals().get("USERS_FILE", "data/users.json")
    admin_password = os.environ.get("ADMIN_PASSWORD", "").strip()

    if admin_password and os.path.exists(users_file):
        try:
            with open(users_file, "r", encoding="utf-8") as f:
                users = json.load(f)

            if "admin" in users:
                users["admin"]["password"] = admin_password
                with open(users_file, "w", encoding="utf-8") as f:
                    json.dump(users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("ENV_OVERRIDE_ERROR:", e)

apply_runtime_env_overrides()''',
    text,
    count=1
)

text = re.sub(
    r'app\.secret_key\s*=\s*.*',
    'app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-change-this-now")',
    text
)

text = re.sub(
    r'app\.config\[\s*["\']SECRET_KEY["\']\s*\]\s*=\s*.*',
    'app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-change-this-now")',
    text
)

text = text.replace(
    'import os\nport = int(os.environ.get("PORT", 5000))\napp.run(host="0.0.0.0", port=port)',
    'port = int(os.environ.get("PORT", 5000))\nlocal_debug = os.environ.get("FLASK_DEBUG", "0") == "1"\napp.run(host="0.0.0.0", port=port, debug=local_debug)'
)

text = text.replace(
    'app.run(host="0.0.0.0", port=5000, debug=True)',
    'port = int(os.environ.get("PORT", 5000))\n    local_debug = os.environ.get("FLASK_DEBUG", "0") == "1"\n    app.run(host="0.0.0.0", port=port, debug=local_debug)'
)

p.write_text(text, encoding="utf-8")
print("OK: Render security patch uygulandı.")
