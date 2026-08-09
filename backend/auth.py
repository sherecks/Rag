"""
Autenticação simples de usuário único (admin) por sessão em memória.

Credenciais vêm de variáveis de ambiente (AUTH_EMAIL / AUTH_PASSWORD), com
fallback para as credenciais padrão do projeto — configure-as no Railway para
usar (ou trocar) essas credenciais em produção.
"""

import hmac
import os
import secrets

from fastapi import HTTPException, Request

AUTH_EMAIL = os.environ.get("AUTH_EMAIL", "admin@karagua.com.br")
AUTH_PASSWORD = os.environ.get("AUTH_PASSWORD", "123456")

SESSION_COOKIE_NAME = "karagua_session"

_active_sessions: set[str] = set()


def check_credentials(email: str, password: str) -> bool:
    return hmac.compare_digest(email or "", AUTH_EMAIL) and hmac.compare_digest(password or "", AUTH_PASSWORD)


def create_session() -> str:
    token = secrets.token_urlsafe(32)
    _active_sessions.add(token)
    return token


def destroy_session(token: str | None) -> None:
    if token:
        _active_sessions.discard(token)


def is_valid_session(token: str | None) -> bool:
    return bool(token and token in _active_sessions)


async def require_auth(request: Request) -> None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not is_valid_session(token):
        raise HTTPException(status_code=401, detail="Não autenticado.")
