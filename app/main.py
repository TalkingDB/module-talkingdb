from fastapi import FastAPI
from app.api import root, index, extract
from app.services.workers import start_workers
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import threading


@asynccontextmanager
async def lifespan(app: FastAPI):
    threading.Thread(target=start_workers, daemon=True).start()
    yield
    # Shutdown code can go here


app = FastAPI(lifespan=lifespan, title="Module TalkingDB")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(root.router)
app.include_router(index.router)
app.include_router(extract.router)
