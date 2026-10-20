import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict
from serpapi import SerpApiClient
from tools import ToolExecutor

load_dotenv()

def search(query: str) -> str:
     """
     A web search engine tool based on SerpApi
     """
     print(f"🔍 Executing [SerpApi] web search: {query}")
     try:
          api_key = os.getenv("SERPAPI_API_KEY")
          if not api_key:
               return "Error: SERPAPI_API_KEY not configured in the .env file."
          
          params = {
               "engine": "google",
               "q": query,
               "api_key": api_key,
               "hl": "en",
               "gl": "us"
          }
          
          client = SerpApiClient(params)
          results = client.get_dict()
          
          # Intelligent parsing: prioritize the most direct answer
          if "answer_box_list" in results:
            return "\n".join(results["answer_box_list"])
          if "answer_box" in results and "answer" in results["answer_box"]:
            return results["answer_box"]["answer"]
          if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            return results["knowledge_graph"]["description"]
          if "organic_results" in results and results["organic_results"]:
            # If no direct answer, return summaries of the first three organic results
            snippets = [
                f"[{i+1}] {res.get('title', '')}\n{res.get('snippet', '')}"
                for i, res in enumerate(results["organic_results"][:3])
            ]
            return "\n\n".join(snippets)
        
          return f"Sorry, no information found about '{query}'."
     
     except Exception as e:
          # Some HTTP client errors include the full request URL, including its API key.
          return f"Error occurred during search ({type(e).__name__})."


class HelloAgent:
     
     def __init__(self, model: str = None, api_key: str = None, base_url: str = None, timeout: int = None):
        """
        Initializes the HelloAgent with the specified model, API key, base URL, and timeout. 
        If any of these parameters are not provided, they will be fetched from environment variables.
        """
        
        self.model = model or os.getenv("LLM_MODEL_ID")
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL")
        self.timeout = timeout or int(os.getenv("LLM_TIMEOUT", 60))
        if not all([self.model, self.api_key, self.base_url]):
            raise ValueError("Model, API key, and base URL must be provided.")
        
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
     
     def run(self, messages: List[Dict[str, str]], temperature: float = 0) -> str:
          """
          Run the model with the provided messages and return the response.
          """
          try:
               response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    timeout=self.timeout,
                    stream=True
               )
               # Collect the streamed response
               collected_response = []
               for chunk in response:
                    if not chunk.choices:
                         continue
                    content = chunk.choices[0].delta.content or ""
                    print(content, end="", flush=True)  # Print the content as it arrives
                    collected_response.append(content)
               print()  # Print a newline after the response is complete
               return ''.join(collected_response)
          except Exception as e:
               return str(e)
     

if __name__=='__main__':
     # 1. Initialize tool executor
     toolExecutor = ToolExecutor()

     # 2. Register our practical search tool
     search_description = (
          "A web search engine. Use this tool when you need to answer questions "
          "about current events, facts, and information not found in your knowledge base."
     )
     toolExecutor.registerTool("Search", search_description, search)

     # 3. Print available tools
     print("\n--- Available Tools ---")
     print(toolExecutor.getAvailableTools())

     # 4. Execute a real-time tool action
     print("\n--- Execute Action: Search['What is NVIDIA's latest GPU model'] ---")
     tool_name = "Search"
     tool_input = "What is NVIDIA's latest GPU model"

     tool_function = toolExecutor.getTool(tool_name)
     if tool_function:
          observation = tool_function(tool_input)
          print("--- Observation ---")
          print(observation)
     else:
          print(f"Error: Tool named '{tool_name}' not found.")
          
