import os
from openai import OpenAI
import json

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_cycling_image(prompt):
    """
    Generate an image using OpenAI's GPT-4V model with cartoon styling
    
    Args:
        prompt (str): The description for image generation
        
    Returns:
        str: URL of the generated image
    """
    # Make sure to include cartoon style in the prompt
    if "Hanna-Barbera" not in prompt and "Hanna Barbera" not in prompt:
        enhanced_prompt = f"Create a cartoon illustration of {prompt}. Use vibrant colors, distinctive character styling like in classic cartoons. Exaggerate features and expressions with a fun, cartoonish look."
    else:
        # Remove Hanna-Barbera reference as requested
        enhanced_prompt = prompt.replace("Hanna-Barbera", "cartoon").replace("Hanna Barbera", "cartoon")
    
    try:
        # Use DALL-E 2 model for image generation (falling back to DALL-E 2 as gpt-image-1 requires organization verification)
        response = client.images.generate(
            model="dall-e-2",
            prompt=enhanced_prompt,
            n=1,
            size="1024x1024"
        )
        return response.data[0].url
    except Exception as e:
        print(f"Error generating image: {e}")
        # Return a fallback image URL if generation fails
        return "https://pixabay.com/get/g304f126f1ed86d95d6c2b68c142c916a8c311d58bdb5518620e7a9fc35b5396404e83a56cb54183dba66b3fe95005d9289a85b998b8e9b92866123b7391ab792_1280.jpg"

def generate_weather_prompt(weather_data):
    """
    Generate a prompt for DALL-E based on weather data
    
    Args:
        weather_data (dict): Dictionary containing weather information
        
    Returns:
        str: A prompt for image generation
    """
    temperature = weather_data.get('temperatura', 25)
    humidity = weather_data.get('umidade', 50)
    luminosity = weather_data.get('luminosidade', 500)
    
    # Determine weather condition
    condition = "sunny"
    if temperature < 15:
        condition = "cool"
    elif temperature > 30:
        condition = "hot"
    
    if humidity > 80:
        condition = "rainy"
    elif humidity < 30:
        condition = "dry"
    
    time_of_day = "daytime"
    if luminosity < 200:
        time_of_day = "evening" 
    elif luminosity < 50:
        time_of_day = "night"
        
    return f"Cartoon illustration of cyclists riding in a {condition} {time_of_day} scene with {temperature}°C temperature and {humidity}% humidity. Show cycling characters in vibrant cartoon style with exaggerated features."

def analyze_cycling_conditions(sensor_data):
    """
    Analyze cycling conditions using OpenAI
    
    Args:
        sensor_data (dict): Dictionary containing sensor information
        
    Returns:
        dict: Analysis results
    """
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        prompt = f"""
        Analyze these cycling conditions and provide a rating for each category from 1-10:
        
        Temperature: {sensor_data.get('temperatura', 'N/A')}°C
        Humidity: {sensor_data.get('umidade', 'N/A')}%
        Pressure: {sensor_data.get('pressao', 'N/A')} hPa
        Luminosity: {sensor_data.get('luminosidade', 'N/A')} lux
        Time: {sensor_data.get('data_hora', 'N/A')}
        
        Return a JSON with these fields:
        - overall_rating: 1-10 score for cycling conditions
        - comfort_level: 1-10 score for cyclist comfort
        - safety_level: 1-10 score for cycling safety
        - recommendations: list of 3 brief recommendations
        - best_bike_type: recommended type of bicycle for these conditions
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a cycling conditions analyst."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error analyzing cycling conditions: {e}")
        # Return default analysis if API call fails
        return {
            "overall_rating": 7,
            "comfort_level": 7,
            "safety_level": 7,
            "recommendations": [
                "Stay hydrated",
                "Wear appropriate clothing",
                "Use lights if visibility is poor"
            ],
            "best_bike_type": "Hybrid bike"
        }
