import hashlib
import hmac
import json
import re
import secrets
from pathlib import Path

USERS_FILE = Path(__file__).parent / "users.json"


def _load() -> dict:
    try:
        return json.loads(USERS_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _hash(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000).hex()


def signup(name: str, email: str, password: str):
    email = email.strip().lower()
    if not name.strip():
        return False, "Enter your name."
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return False, "Enter a valid email address."
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    users = _load()
    if email in users:
        return False, "An account with this email already exists. Log in instead."
    salt = secrets.token_bytes(16)
    users[email] = {"name": name.strip(), "salt": salt.hex(), "hash": _hash(password, salt)}
    USERS_FILE.write_text(json.dumps(users, indent=2))
    return True, name.strip()


def login(email: str, password: str):
    user = _load().get(email.strip().lower())
    if not user:
        return False, "Email or password is incorrect."
    expected = _hash(password, bytes.fromhex(user["salt"]))
    if not hmac.compare_digest(expected, user["hash"]):
        return False, "Email or password is incorrect."
    return True, user["name"]
