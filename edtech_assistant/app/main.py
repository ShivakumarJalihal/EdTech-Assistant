# FILE: app/main.py

from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
# This is the line that was missing
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

# Import our services and models
from app.core.rag_service import RAGService
from app.agents.manager_agent import ManagerAgent
from app.core import models
from app.core.db import engine, get_db
from app.core.models import Conversation

# This dictionary will hold our initialized services
app_state = {}

# Use FastAPI's lifespan context manager to initialize services on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    print("INFO:     Application startup...")
    print("INFO:     Initializing RAG Service...")
    app_state["rag_service"] = RAGService()
    print("INFO:     RAG Service Initialized.")
    print("INFO:     Initializing Manager Agent...")
    app_state["manager_agent"] = ManagerAgent(rag_service_instance=app_state["rag_service"])
    print("INFO:     Manager Agent Initialized.")
    yield
    # On shutdown
    print("INFO:     Application shutdown...")
    app_state.clear()

# Pass the lifespan manager to the FastAPI app
app = FastAPI(title="Multi-Agent EdTech Assistant", lifespan=lifespan)

# --- Database Table Creation ---
try:
    models.Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"ERROR: Could not create database tables: {e}")
    pass

# This line will now work because Jinja2Templates is imported
templates = Jinja2Templates(directory="app/templates")

class ChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
async def chat(chat_request: ChatRequest, db: Session = Depends(get_db)):
    # Get the initialized manager agent from the app_state
    manager = app_state["manager_agent"]
    conversation_id = chat_request.conversation_id

    if conversation_id is None:
        new_conversation = Conversation()
        db.add(new_conversation)
        db.commit()
        db.refresh(new_conversation)
        conversation_id = new_conversation.id

    response_text = manager.process_query(chat_request.message, db, conversation_id)

    return JSONResponse({
        "response": response_text,
        "conversation_id": conversation_id
    })