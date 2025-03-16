"""
Weather agent using PydanticAI with Groq LLM integration.
This agent gets weather data for locations using external APIs.
"""

from __future__ import annotations as _annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import logfire
from httpx import AsyncClient

from pydantic_ai import Agent, ModelRetry, RunContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logfire with conditional sending
try:
    logfire.configure(send_to_logfire='if-token-present')
except Exception:
    # Fallback if logfire isn't properly configured
    pass

@dataclass
class Deps:
    client: AsyncClient
    weather_api_key: str | None
    geo_api_key: str | None

# Create a weather agent using Groq's LLama model
# Note the 'groq:' prefix for using Groq models with PydanticAI
weather_agent = Agent(
    'groq:llama-3.1-70b-versatile',  # Using Groq's LLama 3 70B model
    system_prompt=(
        'Be concise, reply with one sentence. '
        'Use the `get_lat_lng` tool to get the latitude and longitude of the locations, '
        'then use the `get_weather` tool to get the weather for each location. '
        'Include temperature and weather conditions in your response.'
    ),
    deps_type=Deps,
    retries=2,
)

@weather_agent.tool
async def get_lat_lng(
    ctx: RunContext[Deps], location_description: str
) -> dict[str, float]:
    """Get the latitude and longitude of a location.

    Args:
        ctx: The context object containing dependencies.
        location_description: A description of a location (city, address, etc).

    Returns:
        A dictionary with 'lat' and 'lng' keys containing the coordinates.
    """
    if ctx.deps.geo_api_key is None:
        # Return dummy data if no API key is provided
        print(f"Using dummy geocode data for: {location_description}")
        # Different dummy locations based on common cities
        if "bangkok" in location_description.lower():
            return {'lat': 13.7563, 'lng': 100.5018}
        elif "london" in location_description.lower():
            return {'lat': 51.5074, 'lng': -0.1278}
        elif "new york" in location_description.lower():
            return {'lat': 40.7128, 'lng': -74.0060}
        else:
            return {'lat': 51.1, 'lng': -0.1}  # Default location

    params = {
        'q': location_description,
        'api_key': ctx.deps.geo_api_key,
    }
    
    try:
        with logfire.span('calling geocode API', params=params) as span:
            r = await ctx.deps.client.get('https://geocode.maps.co/search', params=params, timeout=10.0)
            r.raise_for_status()
            data = r.json()
            
            if span:  # Only log if span exists (logfire is configured)
                span.set_attribute('response', data)
    except Exception as e:
        print(f"Error calling geocode API: {e}")
        raise ModelRetry(f'Error getting location coordinates: {e}')

    if data and len(data) > 0:
        return {'lat': float(data[0]['lat']), 'lng': float(data[0]['lon'])}
    else:
        raise ModelRetry(f'Could not find coordinates for location: {location_description}')

@weather_agent.tool
async def get_weather(ctx: RunContext[Deps], lat: float, lng: float) -> dict[str, Any]:
    """Get the current weather at a specific location.

    Args:
        ctx: The context object containing dependencies.
        lat: Latitude of the location.
        lng: Longitude of the location.

    Returns:
        A dictionary containing weather information including temperature and conditions.
    """
    if ctx.deps.weather_api_key is None:
        # Return dummy data if no API key is provided
        print(f"Using dummy weather data for coordinates: {lat}, {lng}")
        # Vary the dummy data based on coordinates to seem more realistic
        if lat > 40:  # Northern locations
            return {'temperature': '15 °C', 'description': 'Partly Cloudy'} 
        elif lat > 30:  # Mid latitudes
            return {'temperature': '21 °C', 'description': 'Sunny'}
        else:  # Tropical areas
            return {'temperature': '32 °C', 'description': 'Hot and Humid'}

    params = {
        'apikey': ctx.deps.weather_api_key,
        'location': f'{lat},{lng}',
        'units': 'metric',
    }
    
    try:
        with logfire.span('calling weather API', params=params) as span:
            r = await ctx.deps.client.get(
                'https://api.tomorrow.io/v4/weather/realtime', 
                params=params,
                timeout=10.0
            )
            r.raise_for_status()
            data = r.json()
            
            if span:  # Only log if span exists (logfire is configured)
                span.set_attribute('response', data)
    except Exception as e:
        print(f"Error calling weather API: {e}")
        raise ModelRetry(f'Error getting weather data: {e}')

    # Weather code lookup for Tomorrow.io API
    # https://docs.tomorrow.io/reference/data-layers-weather-codes
    code_lookup = {
        1000: 'Clear, Sunny',
        1100: 'Mostly Clear',
        1101: 'Partly Cloudy',
        1102: 'Mostly Cloudy',
        1001: 'Cloudy',
        2000: 'Fog',
        2100: 'Light Fog',
        4000: 'Drizzle',
        4001: 'Rain',
        4200: 'Light Rain',
        4201: 'Heavy Rain',
        5000: 'Snow',
        5001: 'Flurries',
        5100: 'Light Snow',
        5101: 'Heavy Snow',
        6000: 'Freezing Drizzle',
        6001: 'Freezing Rain',
        6200: 'Light Freezing Rain',
        6201: 'Heavy Freezing Rain',
        7000: 'Ice Pellets',
        7101: 'Heavy Ice Pellets',
        7102: 'Light Ice Pellets',
        8000: 'Thunderstorm',
    }
    
    values = data['data']['values']
    
    return {
        'temperature': f'{values["temperatureApparent"]:0.1f}°C',
        'description': code_lookup.get(values['weatherCode'], 'Unknown'),
        'humidity': f'{values.get("humidity", 0)}%',
        'windSpeed': f'{values.get("windSpeed", 0)} m/s',
        'weatherCode': values['weatherCode'],
    }

async def get_weather_for_locations(locations: List[str]) -> Dict[str, Any]:
    """
    Get weather for multiple locations using the PydanticAI agent with Groq.
    
    Args:
        locations: List of location names
        
    Returns:
        Dict with weather information and LLM response
    """
    # Create dependencies
    async with AsyncClient() as client:
        deps = Deps(
            client=client,
            weather_api_key=os.getenv('WEATHER_API_KEY'),
            geo_api_key=os.getenv('GEO_API_KEY')
        )
        
        # Format prompt for locations
        if len(locations) == 1:
            prompt = f"What is the current weather in {locations[0]}?"
        else:
            locations_str = ", ".join(locations[:-1]) + " and " + locations[-1]
            prompt = f"What is the current weather in {locations_str}?"
        
        print(f"Querying weather agent with prompt: {prompt}")
        
        # Run the agent with reasonable timeout
        try:
            result = await asyncio.wait_for(
                weather_agent.run(prompt, deps=deps),
                timeout=45.0
            )
            
            # Return the data (LLM response)
            return {
                'response': result.data,
                'locations': locations,
                'success': True
            }
        except Exception as e:
            print(f"Error running weather agent: {e}")
            return {
                'response': f"Sorry, I couldn't get the weather information at this time.",
                'locations': locations,
                'success': False,
                'error': str(e)
            }

# Test function to run the agent directly
async def main():
    async with AsyncClient() as client:
        weather_api_key = os.getenv('WEATHER_API_KEY')
        geo_api_key = os.getenv('GEO_API_KEY')
        
        deps = Deps(
            client=client, 
            weather_api_key=weather_api_key, 
            geo_api_key=geo_api_key
        )
        
        result = await weather_agent.run(
            'What is the weather like in Bangkok and in New York?', 
            deps=deps
        )
        
        print('Response:', result.data)

if __name__ == '__main__':
    asyncio.run(main())