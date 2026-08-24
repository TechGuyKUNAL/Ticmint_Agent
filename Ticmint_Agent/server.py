import os
import json
import requests
import gspread
from google.oauth2.service_account import Credentials
from fastmcp import FastMCP

# This creates your custom MCP Server
mcp = FastMCP("TicmintListener")

@mcp.tool
def fetch_reddit_posts(subreddit: str, limit: int = 20) -> str:
    """Fetch recent posts from a specific subreddit to find complaints."""
    url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"
    headers = {"User-Agent": "TicmintGrowthAgent/1.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return json.dumps({"error": "Failed to fetch data."})
    
    posts = []
    data = response.json().get("data", {}).get("children", [])
    for post in data:
        p = post["data"]
        if p.get("selftext"): # Only grab text posts
            posts.append({
                "title": p.get("title"),
                "content": p.get("selftext"),
                "url": f"https://reddit.com{p.get('permalink')}",
                "author": p.get("author")
            })
    return json.dumps(posts)

@mcp.tool
def save_lead_to_sheet(author: str, url: str, pain_point: str, outreach_draft: str) -> str:
    """Save a qualified lead to Google Sheets."""
    creds_json = os.environ.get("GCP_CREDENTIALS")
    creds_dict = json.loads(creds_json)
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    
    sheet_id = os.environ.get("SHEET_ID")
    sheet = client.open_by_key(sheet_id).sheet1
    
    sheet.append_row([author, url, pain_point, outreach_draft])
    return f"Successfully saved lead {author} to sheet."

if __name__ == "__main__":
    mcp.run()
