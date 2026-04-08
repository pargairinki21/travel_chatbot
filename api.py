import os
import json
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.adk.runners import InMemoryRunner
from google.genai import types
from agents import travel_system
from tools import find_travel_destinations
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

runner = None
SESSION_ID = "web-session-1"
USER_ID = "web-user-1"

@app.on_event("startup")
async def startup():
    global runner
    runner = InMemoryRunner(agent=travel_system)
    await runner.session_service.create_session(
        app_name=runner.app_name,
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    print("Travel agent ready!")

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(request: ChatRequest):
    content = types.Content(
        role="user",
        parts=[types.Part(text=request.message)]
    )
    final_response = "No response generated."
    try:
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response = event.content.parts[0].text
                break
    except Exception as e:
        final_response = f"Error: {str(e)}"
    return {"response": final_response}

@app.post("/places")
async def places(request: ChatRequest):
    """Returns raw place data with lat/lon for map pins."""
    message = request.message.lower()


    city = request.message
    
    match = re.search(r"(?:near|from|in|at|to)\s+([a-zA-Z\s]+)", message)
    if match:
        city = match.group(1).strip()
    else:
        
        city = message.replace("nearest", "").replace("beach", "").replace("hill", "").strip()

    
    city = city.split("show")[0].split("?")[0].split(".")[0].strip()
    
    
    city = city.title()

    
    try:
        raw = find_travel_destinations(city)
        data = json.loads(raw)
        
        
        if "error" in data:
            return {"city": city, "mountains": [], "beaches": [], "note": data["error"]}
            
    except Exception as e:
        print(f"Error calling tool: {e}")
        return {"city": city, "mountains": [], "beaches": [], "error": "Internal search failure"}

    
    asking_beach = any(w in message for w in ["beach", "sea", "coast", "ocean", "water"])
    asking_mountain = any(w in message for w in ["mountain", "hill", "hills", "trek", "trekking", "peak", "station"])

    if asking_beach and not asking_mountain:
        data["mountains"] = []
    elif asking_mountain and not asking_beach:
        data["beaches"] = []

    return data

@app.get("/health")
async def health():
    return {"status": "ok"}