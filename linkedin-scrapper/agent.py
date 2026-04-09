import os
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import json
import re

from tools.linkedin import scrape_profile, search_linkedin, init_tools
from core.browser import BrowserManager
from core.auth import load_cookies, perform_auto_login, save_cookies

load_dotenv()

class LinkedInAgent:
    def __init__(self):
        self.browser_manager = None
        self.model = None

    async def initialize(self):
        cookies_path = os.getenv("LINKEDIN_COOKIES_PATH", "cookies.json")
        cookies = load_cookies(cookies_path)
        
        self.browser_manager = BrowserManager()
        await self.browser_manager.start(cookies=cookies)
        init_tools(self.browser_manager)
        
        from langchain_ollama import ChatOllama
        # Initialize LLM
        self.model = ChatOllama(model="mistral", temperature=0)
        
        # Perform an initial check
        print("Checking LinkedIn login status...")
        await self.browser_manager.navigate("https://www.linkedin.com/feed/")
        await self.browser_manager.human_delay(3, 5)
        
        curr_url = self.browser_manager.page.url
        if "login" in curr_url or "checkpoint" in curr_url or "signup" in curr_url:
            print("Session invalid or cookies missing.")
            username = os.getenv("LINKEDIN_USERNAME")
            password = os.getenv("LINKEDIN_PASSWORD")
            
            if username and password:
                await perform_auto_login(self.browser_manager, username, password, cookies_path)
            else:
                print("No LINKEDIN_USERNAME/LINKEDIN_PASSWORD found in .env.")
                print("You must log in manually in the browser window!")
                input("Log in manually in the popup browser window, then press Enter here to continue...")
                
                # Save cookies for the future
                cookies = await self.browser_manager.get_cookies()
                save_cookies(cookies, cookies_path)
        
    async def run(self, query):
        print(f"\n--- Running Query: {query} ---\n")
        
        sys_msg = (
            "You are a LinkedIn Scraping Agent that retrieves REAL data from LinkedIn.\n\n"
            "## CRITICAL RULES:\n"
            "- You MUST call a tool FIRST before answering. NEVER answer from imagination.\n"
            "- NEVER fabricate, invent, or hallucinate any data, names, companies, or job postings.\n"
            "- If asked about a topic, use search_linkedin to find REAL posts/discussions about it.\n"
            "- ONLY summarize data that was returned by a tool. If no data was returned, say so.\n\n"
            "## Available Tools:\n\n"
            "1. **search_linkedin**(query: str) — Searches LinkedIn.\n"
            '   Usage: ```json\n[{"name": "search_linkedin", "arguments": {"query": "your search terms"}}]\n```\n\n'
            "2. **scrape_profile**(url: str) — Scrapes a LinkedIn profile/company page. Requires a REAL full URL.\n"
            '   Usage: ```json\n[{"name": "scrape_profile", "arguments": {"url": "https://www.linkedin.com/in/someone/"}}]\n```\n\n'
            "## FORMAT RULES:\n"
            "- To call a tool: output EXACTLY ONE tool call in a ```json block. Nothing else.\n"
            "- Do NOT add explanations before or after the JSON block when calling a tool.\n"
            "- After receiving results: write a DETAILED summary using ONLY the returned data.\n"
            "- Include specific names, titles, companies, and details from the results.\n"
        )
        
        messages = [
            SystemMessage(content=sys_msg),
            HumanMessage(content=query)
        ]
        
        PLACEHOLDERS = {"PROFILE_ID", "URL", "PLACEHOLDER", "EXAMPLE", "YOUR_"}
        
        for step in range(3): # Max 3 turns to prevent infinite loops
            try:
                response = await self.model.ainvoke(messages)
                content = response.content
                print(f"\n\033[94mAgent:\033[0m\n{content}")
                
                messages.append(AIMessage(content=content))
                
                # Extract JSON blocks
                json_blocks = re.findall(r'```(?:json|javascript)\n(.*?)\n```', content, re.DOTALL)
                if not json_blocks:
                    json_blocks = re.findall(r'(\[\s*\{\s*"name".*?\}\s*\])', content, re.DOTALL)
                    
                if not json_blocks:
                    break # No tool calls, this is the final answer
                    
                raw_json = json.loads(json_blocks[0])
                flat_tool_calls = []
                
                # Recursively flatten any hallucinated nested lists/dicts
                def extract_tools(data):
                    if isinstance(data, list):
                        for item in data: extract_tools(item)
                    elif isinstance(data, dict):
                        if "name" in data: flat_tool_calls.append(data)
                        else:
                            for v in data.values(): extract_tools(v)
                extract_tools(raw_json)

                # Execute only the FIRST valid tool call per turn
                executed = False
                for tc in flat_tool_calls:
                    if executed:
                        break
                    name = tc.get("name")
                    args = tc.get("arguments", {})
                    
                    # Skip any tool calls with placeholder values
                    arg_values = str(args).upper()
                    if any(p in arg_values for p in PLACEHOLDERS):
                        print(f"\n\033[93mSkipped:\033[0m {name} — contains placeholder values.")
                        continue
                    
                    print(f"\n\033[92mTools:\033[0m Executing {name}({args})...")
                    
                    try:
                        if name == "search_linkedin":
                            res = await search_linkedin.ainvoke(args)
                        elif name == "scrape_profile":
                            res = await scrape_profile.ainvoke(args)
                        else:
                            res = f"Unknown tool: {name}"
                        
                        messages.append(HumanMessage(
                            content=f"Tool Result from {name}:\n{res}\n\nNow summarize this data for the user in plain text. Do NOT output any more JSON."
                        ))
                        executed = True
                    except Exception as tool_err:
                        print(f"\n\033[91mTool Error:\033[0m {tool_err}")
                        messages.append(HumanMessage(
                            content=f"Tool {name} failed: {tool_err}. Summarize what you know so far in plain text."
                        ))
                        executed = True
                        
                if not executed:
                    messages.append(HumanMessage(
                        content="All tool calls were invalid. Please answer the user's question using your general knowledge in plain text."
                    ))
                
            except json.JSONDecodeError as je:
                print(f"\n\033[91mJSON Parse Error:\033[0m {je}")
                break
            except Exception as e:
                print(f"\n\033[91mError:\033[0m {e}")
                break
            
    async def cleanup(self):
        if self.browser_manager:
            await self.browser_manager.close()
