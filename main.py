import asyncio
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.adk.runners import InMemoryRunner
from google.genai import types
from agents import travel_system
from dotenv import load_dotenv

# 1. Load your local keys (if any)
load_dotenv()

# 2. Initialize the FastAPI Web Engine
app = FastAPI()

# 3. Security: Allow your frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Your original logic & IDs
USER_ID = "user-1"
SESSION_ID = "session-1"
runner = InMemoryRunner(agent=travel_system)

# 5. Startup logic: This replaces your "while True" loop start
@app.on_event("startup")
async def startup_event():
    await runner.session_service.create_session(
        app_name=runner.app_name,
        user_id=USER_ID,
        session_id=SESSION_ID
    )

# 6. Data structure for the chat message
class ChatRequest(BaseModel):
    message: str

# 7. The Web Entry Point: This replaces your "input()" and "print()"
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    content = types.Content(
        role='user',
        parts=[types.Part(text=request.message)]
    )
    
    final_response = "No response generated."
    try:
        # Your original async runner logic
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response = event.content.parts[0].text
                break
        
        # Return the answer to your website
        return {"response": final_response}
        
    except Exception as e:
        return {"response": f"Error: {str(e)}"}

# 8. A "Heartbeat" link to check if it's alive (open your Render URL to see this)
@app.get("/")
def read_root():
    return {"status": "Travel Agent API is Live and Running!"}