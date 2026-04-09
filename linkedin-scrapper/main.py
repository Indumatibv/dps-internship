import sys
import os
import asyncio
from agent import LinkedInAgent

async def run_app():
    print("Welcome to the LinkedIn Scraper Agent!")
    
    if not os.path.exists(".env"):
         print("Note: .env file not found. You can copy .env.example to .env to set LINKEDIN_USERNAME for auto-login.")
         
    if not os.path.exists("cookies.json"):
         print("Warning: cookies.json not found. The browser will likely be redirected to the login page.")
         print("Please export your LinkedIn cookies using a browser extension (like EditThisCookie) and save it as cookies.json.")
         
    agent = LinkedInAgent()
    try:
        print("\nInitializing browser and agent...")
        await agent.initialize()
        
        print("\nAgent is ready! Type 'exit' or 'quit' to close.")
        while True:
            # We use an executor to prevent input() from blocking the asyncio loop completely, 
            # though it's not strictly necessary for this simple script natively
            query = await asyncio.to_thread(input, "\nEnter your request (e.g., 'Search for Python Developers'): ")
            if query.lower() in ['exit', 'quit']:
                break
                
            if query.strip():
                await agent.run(query)
                
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        await agent.cleanup()

def main():
    asyncio.run(run_app())

if __name__ == "__main__":
    main()
