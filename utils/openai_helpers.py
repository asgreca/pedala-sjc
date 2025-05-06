import os
import base64
from openai import OpenAI
import json

# Get API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_hanna_barbera_image(prompt):
    """
    Generate an image in Hanna Barbera style using DALL-E
    
    Parameters:
    - prompt (str): Text description of the image to generate
    
    Returns:
    - dict: Contains URL of the generated image
    """
    complete_prompt = (
        f"Create a colorful cartoon illustration in classic Hanna Barbera style: {prompt}. "
        "Use bright colors, simple shapes, and the characteristic Hanna Barbera animation style "
        "from classics like The Flintstones, Scooby-Doo, and The Jetsons. Make it cheerful and "
        "appealing with clean lines and vibrant colors."
    )
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=complete_prompt,
            n=1,
            size="1024x1024"
        )
        return {"url": response.data[0].url, "success": True}
    except Exception as e:
        print(f"Error generating image: {e}")
        return {"url": "", "success": False, "error": str(e)}

def get_cycling_prompts(weather_data, user_level, distance):
    """
    Generate prompts for illustrations based on the current weather and user preferences
    
    Parameters:
    - weather_data (dict): Current weather/sensor data
    - user_level (str): User's cycling level
    - distance (int): Desired cycling distance
    
    Returns:
    - list: List of image prompts tailored to the conditions
    """
    # Base on temperature and time of day
    temp = weather_data.get('temperatura', 25)
    humidity = weather_data.get('umidade', 50)
    luminosity = weather_data.get('luminosidade', 500)
    
    time_of_day = "daytime"
    if luminosity < 300:
        time_of_day = "evening"
    if luminosity < 100:
        time_of_day = "night"
    
    weather_type = "sunny"
    if humidity > 80:
        weather_type = "rainy"
    if temp < 15:
        weather_type = "cold"
    if temp > 30:
        weather_type = "hot"
    
    prompts = [
        f"A {user_level.lower()} cyclist biking through a {weather_type} {time_of_day} scenery",
        f"Cartoon character preparing for a {distance}km bike ride in {weather_type} weather",
        f"Cycling group enjoying a {weather_type} day on their bicycles in the park"
    ]
    
    return prompts

def generate_sensor_simulation(current_data=None):
    """
    Generate simulated sensor data if needed
    
    Parameters:
    - current_data (dict): Existing data to base simulations on
    
    Returns:
    - dict: Simulated sensor data
    """
    # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
    # do not change this unless explicitly requested by the user
    prompt = """Generate realistic sensor data for cycling in São José dos Campos, Brazil.
    Return a JSON with these fields:
    - "temperatura": temperature in °C (float)
    - "umidade": humidity percentage (float)
    - "pressao": pressure in hPa (float)
    - "luminosidade": brightness in lux (float)
    - "vento": wind speed in km/h (float)
    - "indice_uv": UV index (float)
    - "qualidade_ar": air quality index (float)
    Make the values realistic and appropriate for the current season."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a weather and environmental sensor data generator for cycling applications."},
                {"role": "user", "content": prompt}
            ]
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error generating sensor data: {e}")
        # Return fallback data if API fails
        return {
            "temperatura": 25.0,
            "umidade": 60.0,
            "pressao": 1013.0,
            "luminosidade": 800.0,
            "vento": 12.0,
            "indice_uv": 7.0,
            "qualidade_ar": 45.0
        }
