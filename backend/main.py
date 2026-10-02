"""Vercel / local ASGI entry. Re-exports the FastAPI app."""

from backend.api import app

__all__ = ["app"]
