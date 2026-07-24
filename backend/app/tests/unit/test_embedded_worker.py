import asyncio

from fastapi import FastAPI

from app import worker
from app.main import lifespan, settings


class FakeEngine:
    def __init__(self):
        self.disposed = False

    async def dispose(self):
        self.disposed = True


async def test_lifespan_starts_and_stops_embedded_worker(monkeypatch):
    started = asyncio.Event()
    cancelled = asyncio.Event()
    fake_engine = FakeEngine()

    async def run_worker():
        started.set()
        try:
            await asyncio.Future()
        finally:
            cancelled.set()

    monkeypatch.setattr(settings, "RUN_EMBEDDED_WORKER", True)
    monkeypatch.setattr(worker, "run_worker", run_worker)
    monkeypatch.setattr(worker, "engine", fake_engine)

    async with lifespan(FastAPI()):
        await asyncio.wait_for(started.wait(), timeout=1)

    assert cancelled.is_set()
    assert fake_engine.disposed is True
