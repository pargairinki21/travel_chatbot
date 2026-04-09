from google.adk.agents import Agent, SequentialAgent
from google.adk.models.google_llm import Gemini
from tools import maps_tool, weather_tool
import os
from dotenv import load_dotenv

load_dotenv() # Add this here too!

# Use the environment variable explicitly to be safe
gemini_model = Gemini(model="gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY"))

mapper_agent = Agent(
    name="TechnicalMapper",
    model=gemini_model,
    instruction=(
        "You are a travel logistics expert. "
        "1. Use find_travel_destinations for the user's city. "
        "2. For the closest hill station and closest beach found, use the get_current_weather tool. "
        "3. Pass all mapping and weather data to the CreativeGuide."
    ),
    tools=[maps_tool, weather_tool],
    output_key="raw_travel_data"
)

# ... keep the rest of your guide_agent and travel_system logic ...

guide_agent = Agent(
    name="CreativeGuide",
    model=Gemini(model="gemini-2.5-flash"),
    instruction=(
        "You are a high-end travel concierge. "
        "Use the {raw_travel_data} to build a weekend itinerary. "
        "Crucially, use the weather info to give advice (e.g., 'It's quite warm in Puri, so pack linen'). "
        "Mention the 'Must-Try Food' and 'Vibe' for each place. "
        "Format your output with bold headers, emojis, and clear day-wise steps."
    ),
    output_key="final_itinerary"
)

travel_system = SequentialAgent(
    name="GlobalTravelAgent",
    sub_agents=[mapper_agent, guide_agent]
)