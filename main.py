import asyncio
import os
from google.adk.runners import InMemoryRunner
from google.genai import types
from agents import travel_system
from dotenv import load_dotenv

load_dotenv()

USER_ID = "user-1"
SESSION_ID = "session-1"

async def main():
    runner = InMemoryRunner(agent=travel_system)

    
    await runner.session_service.create_session(
        app_name=runner.app_name,
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    print(" Hello! I am your Universal Travel Agent.")

    while True:
        user_input = input("\nYou (Type 'exit' to quit): ")
        if user_input.lower() in ['exit', 'quit']:
            break

        content = types.Content(
            role='user',
            parts=[types.Part(text=user_input)]
        )

        print("\n--- 🔍 Thinking... ---")

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

            print(f"\nAgent: {final_response}")

        except Exception as e:
            print(f"\n Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())