import requests

def get_weather(city: str) -> str:
     """
        Query real weather information by calling the wttr.in API
     """
     
     # API endpoint
     # request data in JSON format
     url = f"https://wttr.in/{city}?format=j1"
     
     try:
         # make network request
         response = requests.get(url)
         response.raise_for_status()
         
         data = response.json()
         
         # extract current weather conditions
         
     