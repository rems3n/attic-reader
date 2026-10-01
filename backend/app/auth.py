"""Cookie sessions and revision-checked learner documents on persistent storage."""
import hashlib
import json
import os
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

COOKIE = "attic_session"
TTL = 30 * 86400
hasher = PasswordHasher()
DUMMY_HASH = hasher.hash(secrets.token_urlsafe(32))

@contextmanager
def database():
    path = Path(os.getenv("AUTH_DB_PATH", "/data/attic.db" if Path("/data").exists() else "./data/attic.db"))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=15)
    db.row_factory = sqlite3.Row
    try:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY, user_id TEXT NOT NULL, expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS learner_progress (user_id TEXT PRIMARY KEY, document TEXT NOT NULL, revision INTEGER NOT NULL, saved_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS auth_limits (key TEXT PRIMARY KEY, count INTEGER NOT NULL, expires REAL NOT NULL);
        """)
        yield db
        db.commit()
    finally:
        db.close()

def guard(request: Request, response: Response):
    response.headers["Cache-Control"] = "no-store"
    if request.method != "GET" and request.headers.get("x-attic-request") != "1":
        raise HTTPException(403, "Invalid request.")
    origin = request.headers.get("origin")
    allowed = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if origin and origin not in [x.strip() for x in allowed]:
        raise HTTPException(403, "Invalid origin.")

router = APIRouter(prefix="/api", dependencies=[Depends(guard)])
class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)

def email_address(value):
    value = value.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
        raise HTTPException(422, "Enter a valid email address.")
    return value

def throttle(email):
    now = time.time()
    key = hashlib.sha256(email.encode()).hexdigest()
    with database() as db:
        db.execute("DELETE FROM auth_limits WHERE expires < ?", (now,))
        db.execute("INSERT INTO auth_limits VALUES (?, 1, ?) ON CONFLICT(key) DO UPDATE SET count=count+1", (key, now + 900))
        count = db.execute("SELECT count FROM auth_limits WHERE key=?", (key,)).fetchone()[0]
    if count > 15:
        raise HTTPException(429, "Too many attempts. Try again in 15 minutes.")

def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()

def session_user(request):
    with database() as db:
        row = db.execute("SELECT users.id, users.email FROM sessions JOIN users ON users.id=sessions.user_id WHERE token=? AND expires>?", (token_hash(request.cookies.get(COOKIE, "")), time.time())).fetchone()
    if not row:
        raise HTTPException(401, "Sign in to sync your progress.")
    expected = request.headers.get("x-attic-user")
    if expected and expected != row["id"]:
        raise HTTPException(409, "The signed-in account changed. Reload this page.")
    return dict(row)

def start_session(user, request, response):
    token = secrets.token_urlsafe(32)
    with database() as db:
        db.execute("DELETE FROM sessions WHERE expires<? OR token=?", (time.time(), token_hash(request.cookies.get(COOKIE, ""))))
        db.execute("INSERT INTO sessions VALUES (?, ?, ?)", (token_hash(token), user["id"], time.time() + TTL))
    response.set_cookie(COOKIE, token, max_age=TTL, httponly=True, secure=os.getenv("AUTH_COOKIE_SECURE", "true").lower() != "false", samesite="lax", path="/")
    return {"user": user}

@router.post("/auth/signup")
def signup(body: Credentials, request: Request, response: Response):
    email = email_address(body.email)
    throttle(email)
    if len(body.password) < 12:
        raise HTTPException(422, "Use at least 12 characters for your password.")
    user = {"id": secrets.token_hex(16), "email": email}
    password = hasher.hash(body.password)
    try:
        with database() as db:
            db.execute("INSERT INTO users VALUES (?, ?, ?)", (user["id"], email, password))
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Unable to create this account. Try signing in.")
    return start_session(user, request, response)

@router.post("/auth/login")
def login(body: Credentials, request: Request, response: Response):
    email = email_address(body.email)
    throttle(email)
    with database() as db:
        row = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    try:
        hasher.verify(row["password"] if row else DUMMY_HASH, body.password)
    except (VerificationError, InvalidHashError):
        raise HTTPException(401, "Email or password is incorrect.")
    if not row:
        raise HTTPException(401, "Email or password is incorrect.")
    return start_session({"id": row["id"], "email": row["email"]}, request, response)

@router.post("/auth/logout")
def logout(request: Request, response: Response):
    with database() as db:
        db.execute("DELETE FROM sessions WHERE token=?", (token_hash(request.cookies.get(COOKIE, "")),))
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}

@router.get("/me")
def me(request: Request):
    return {"user": session_user(request)}

@router.get("/me/progress")
def get_progress(request: Request):
    user = session_user(request)
    with database() as db:
        row = db.execute("SELECT * FROM learner_progress WHERE user_id=?", (user["id"],)).fetchone()
    return {"document": json.loads(row["document"]) if row else None, "revision": row["revision"] if row else 0, "saved_at": row["saved_at"] if row else None}

class ProgressWrite(BaseModel):
    document: dict
    revision: int = Field(ge=0)

@router.put("/me/progress")
def put_progress(body: ProgressWrite, request: Request):
    user = session_user(request)
    payload = json.dumps(body.document, ensure_ascii=False)
    if len(payload.encode()) > 2 * 1024 * 1024:
        raise HTTPException(413, "Progress document is too large.")
    doc = body.document
    if doc.get("version") != 2 or not all(isinstance(doc.get(k), dict) for k in ("cards", "settings", "course")) or not isinstance(doc.get("log"), list):
        raise HTTPException(422, "Invalid progress document.")
    now = time.time()
    with database() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT revision FROM learner_progress WHERE user_id=?", (user["id"],)).fetchone()
        revision = row[0] if row else 0
        if body.revision != revision:
            raise HTTPException(409, "Progress changed on another device. Retry after merging.")
        db.execute("INSERT INTO learner_progress VALUES (?, ?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET document=excluded.document, revision=excluded.revision, saved_at=excluded.saved_at", (user["id"], payload, revision+1, now))
    return {"revision": revision+1, "saved_at": now}
