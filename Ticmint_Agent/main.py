import asyncio
import os
import json
from fastmcp import Client
from google import genai
from google.genai import types
from pydantic import BaseModel

# Force the AI to output perfect data formats
class Lead(BaseModel):
    author: str
    url: str
    pain_point: str
    outreach_draft: str

class LeadList(BaseModel):
    leads: list[Lead]

async def main():
    print("Starting Ticmint Growth Agent...")
    
    # Initialize the LLM
    ai_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    # Connect to your custom MCP Server
    mcp_client = Client("server.py")
    
    async with mcp_client:
        print("Connected to MCP. Scanning internet...")
        
        # Tool 1: Fetch data (EventProduction is a hub for event organizers)
        reddit_json = await mcp_client.call_tool("fetch_reddit_posts", {"subreddit": "EventProduction", "limit": 25})
        
prompt = f"""
        You are the Growth Lead for Ticmint.
        Read these Reddit posts. I need to test my system, so just pick ANY 2 recent posts from the data, regardless of what they are talking about.
        
        For each match:
        1. Extract their username and URL.
        2. For the 'pain_point', just write a 1-sentence summary of what their post is about.
        3. For 'outreach_draft', just write: "Hey, saw your post about [topic] and wanted to connect!"
        
        Posts Data:
        {reddit_json}
        """
        
        print("Analyzing intent with AI...")
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=LeadList,
                temperature=0.2
            ),
        )
        
        result = response.parsed
        if not result or not result.leads:
            print("No high-intent leads found right now. Exiting.")
            return

        print(f"Found {len(result.leads)} leads! Saving via MCP...")
        for lead in result.leads:
            # Tool 2: Save to Sheet
            await mcp_client.call_tool("save_lead_to_sheet", {
                "author": lead.author,
                "url": lead.url,
                "pain_point": lead.pain_point,
                "outreach_draft": lead.outreach_draft
            })
            print(f"Saved: {lead.author}")

if __name__ == "__main__":
    asyncio.run(main())
