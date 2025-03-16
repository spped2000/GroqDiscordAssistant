import hikari
import lightbulb
import aiohttp
import base64
import re
from typing import Optional, List, Union, Dict, Any
import os
from dotenv import load_dotenv

# Import our Groq-powered PydanticAI weather agent
import weather_agent

load_dotenv()

# Initialize bot with lightbulb
bot = lightbulb.BotApp(
    token=os.getenv("DISCORD_API_KEY"),
    prefix="!"
)

# Groq API configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama3-70b-8192"  # Updated to newer model
DEFAULT_VISION_MODEL = "llama-3.1-8b-vision"  # Using Llama 3.1 for vision

async def fetch_image(url: str) -> Optional[bytes]:
    """
    Fetch an image from a URL.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    print(f"Error fetching image: {response.status}")
                    return None
    except Exception as e:
        print(f"Exception when fetching image: {e}")
        return None

async def query_groq(
    prompt: str, 
    model: str = DEFAULT_MODEL,
    image_urls: List[str] = None
) -> Optional[str]:
    """
    Send a query to the Groq API and return the response.
    Support both text-only and image+text queries.
    """
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Prepare messages for the API call
    messages = []
    
    # If there are image URLs, process them for vision models
    if image_urls and ("vision" in model):
        message_content: List[Dict[str, Any]] = []
        
        # Add the text prompt as the first content item
        message_content.append({
            "type": "text",
            "text": prompt
        })
        
        # Process each image URL and add to content
        for url in image_urls:
            image_data = await fetch_image(url)
            if image_data:
                # Convert image to base64
                base64_image = base64.b64encode(image_data).decode('utf-8')
                
                # Add image content
                message_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                })
        
        # Create the final message with combined content
        messages.append({"role": "user", "content": message_content})
    else:
        # Text-only message
        messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(GROQ_API_URL, headers=headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    print(f"Error from Groq API: {response.status}")
                    error_text = await response.text()
                    print(error_text)
                    return None
    except Exception as e:
        print(f"Exception when calling Groq API: {e}")
        return None

@bot.listen(hikari.GuildMessageCreateEvent)
async def on_message_create(event: hikari.GuildMessageCreateEvent) -> None:
    """
    Listen to all messages and handle mentions, commands, and image attachments.
    """
    # Skip messages from bots
    if not event.is_human:
        return
    
    # Skip messages that aren't in guilds
    if not event.message or not event.message.content:
        return
    
    content = event.message.content
    me = bot.get_me()
    
    # Check if the bot is mentioned
    if me and me.id in event.message.user_mentions_ids:
        # Get the question by removing the mention
        question = content.replace(f"<@{me.id}>", "").strip()
        
        if not question:
            await event.message.respond("Hello! How can I help you today? Ask me any question.")
            return
        
        # Show typing indicator while processing
        await bot.rest.trigger_typing(event.channel_id)
        
        # Check for weather-related questions
        weather_pattern = re.compile(r'weather\s+in\s+([a-zA-Z\s,]+)', re.IGNORECASE)
        weather_match = weather_pattern.search(question)
        
        if weather_match:
            # Extract location(s)
            locations_text = weather_match.group(1)
            locations = [loc.strip() for loc in locations_text.split(",") if loc.strip()]
            
            if locations:
                try:
                    # Show typing indicator again to indicate processing
                    await bot.rest.trigger_typing(event.channel_id)
                    
                    # Get weather using PydanticAI agent with Groq
                    weather_result = await weather_agent.get_weather_for_locations(locations)
                    
                    if weather_result.get('success', False):
                        # Send response from the weather agent
                        await event.message.respond(weather_result['response'])
                    else:
                        # Send error message
                        await event.message.respond("I'm sorry, I couldn't get the weather information at the moment. Please try again later.")
                    return
                except Exception as e:
                    print(f"Error getting weather: {e}")
                    await event.message.respond("I'm sorry, I couldn't get the weather information at the moment. Please try again later.")
                    return
        
        # Check for image attachments
        image_urls = []
        if event.message.attachments:
            for attachment in event.message.attachments:
                if attachment.media_type and attachment.media_type.startswith('image/'):
                    image_urls.append(attachment.url)
        
        # Determine which model to use based on whether images are present
        model = DEFAULT_VISION_MODEL if image_urls else DEFAULT_MODEL
        
        # Get response from Groq
        response = await query_groq(question, model, image_urls)
        
        if response:
            # Send response in chunks if needed
            if len(response) > 2000:
                chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                for chunk in chunks:
                    await event.message.respond(chunk)
            else:
                await event.message.respond(response)
        else:
            await event.message.respond("I'm sorry, I couldn't process your question right now. Please try again later.")

# Command to handle specific model requests
@bot.command
@lightbulb.option("model", "The model to use", required=False, default=DEFAULT_MODEL)
@lightbulb.option("prompt", "Your question or prompt", required=True)
@lightbulb.command("groq", "Ask a question using Groq API")
@lightbulb.implements(lightbulb.PrefixCommand)
async def groq_command(ctx: lightbulb.Context) -> None:
    # Show typing indicator
    await bot.rest.trigger_typing(ctx.channel_id)
    
    # Get response
    response = await query_groq(ctx.options.prompt, ctx.options.model)
    
    if response:
        # Send in chunks if needed
        if len(response) > 2000:
            chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
            for chunk in chunks:
                await ctx.respond(chunk)
        else:
            await ctx.respond(response)
    else:
        await ctx.respond("Sorry, I couldn't get a response from Groq. Please try again later.")

# Command to process images with specific model
@bot.command
@lightbulb.option("model", "The vision model to use", required=False, default=DEFAULT_VISION_MODEL)
@lightbulb.option("prompt", "Your question about the image", required=True)
@lightbulb.command("vision", "Ask a question about the last image you uploaded")
@lightbulb.implements(lightbulb.PrefixCommand)
async def vision_command(ctx: lightbulb.Context) -> None:
    # Show typing indicator
    await bot.rest.trigger_typing(ctx.channel_id)
    
    # Get the channel
    channel = await bot.rest.fetch_channel(ctx.channel_id)
    
    # Fetch recent messages to find the latest image
    messages = await bot.rest.fetch_messages(channel.id, limit=10)
    
    # Find the most recent message with an image from the user
    image_urls = []
    for message in messages:
        if message.author.id == ctx.author.id and message.attachments:
            for attachment in message.attachments:
                if attachment.media_type and attachment.media_type.startswith('image/'):
                    image_urls.append(attachment.url)
                    break
            if image_urls:
                break
    
    if not image_urls:
        await ctx.respond("I couldn't find any recent images you've uploaded. Please upload an image first.")
        return
    
    # Get response
    response = await query_groq(ctx.options.prompt, ctx.options.model, image_urls)
    
    if response:
        # Send in chunks if needed
        if len(response) > 2000:
            chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
            for chunk in chunks:
                await ctx.respond(chunk)
        else:
            await ctx.respond(response)
    else:
        await ctx.respond("Sorry, I couldn't get a response from Groq. Please try again later.")

# Weather command using PydanticAI with Groq
@bot.command
@lightbulb.option("location", "The location(s) to get weather for (comma-separated for multiple)", required=True)
@lightbulb.command("weather", "Get the current weather for a location using PydanticAI with Groq")
@lightbulb.implements(lightbulb.PrefixCommand)
async def weather_command(ctx: lightbulb.Context) -> None:
    try:
        # Show typing indicator
        await bot.rest.trigger_typing(ctx.channel_id)
        
        # Parse locations
        locations = [loc.strip() for loc in ctx.options.location.split(",") if loc.strip()]
        
        if not locations:
            await ctx.respond("Please provide a valid location.")
            return
        
        # Get weather using PydanticAI agent with Groq
        weather_result = await weather_agent.get_weather_for_locations(locations)
        
        if weather_result.get('success', False):
            # Send response
            await ctx.respond(weather_result['response'])
        else:
            # Send error message with any available details
            error_msg = "Sorry, I couldn't get the weather information at the moment."
            if 'error' in weather_result:
                error_msg += f" Error: {weather_result['error']}"
            await ctx.respond(error_msg)
    except Exception as e:
        print(f"Error in weather command: {e}")
        await ctx.respond("Sorry, I couldn't get the weather information at the moment. Please try again later.")

# Command to show available models
@bot.command
@lightbulb.command("models", "Display available Groq models")
@lightbulb.implements(lightbulb.PrefixCommand)
async def models_command(ctx: lightbulb.Context) -> None:
    models_info = """
Available Groq Models:

Text Models:
- llama-3.1-8b-versatile: Meta's Llama 3.1 8B model (fastest)
- llama-3.1-70b-versatile: Meta's Llama 3.1 70B model (more capable, default for text)
- llama-3.1-405b-versatile: Meta's Llama 3.1 405B model (most capable)
- mixtral-8x7b-32768: Mixtral 8x7B model with 32k context
- gemma-7b-it: Google's Gemma 7B model

Vision Models:
- llama-3.1-8b-vision: Llama 3.1 8B vision model (default for images)

Usage:
- Just mention me with your question (with or without attached images)
- Use !groq prompt model:<model> for text-only queries
- Use !vision prompt model:<model> for image queries (uses your most recent image)
- Use !weather location to get current weather information with PydanticAI
    """
    await ctx.respond(models_info)

# Help command
@bot.command
@lightbulb.command("bothelp", "Display bot usage information")
@lightbulb.implements(lightbulb.PrefixCommand)
async def bothelp_command(ctx: lightbulb.Context) -> None:
    help_text = """
I'm your helpful AI assistant powered by Groq LLMs with PydanticAI for weather data!

How to use me:
- Just mention me with your question
- I'll respond to your questions and help with information
- You can also attach images and ask me about them!
- Ask about the weather by mentioning me with "weather in [location]"

Advanced Commands:
- !groq prompt model:<optional_model> - Ask using a specific text model
- !vision prompt model:<optional_model> - Ask about your most recently posted image
- !weather location - Get current weather for a specific location using PydanticAI with Groq
- !models - See available AI models
- !bothelp - Display this help message

Examples:
- @BotName What's the capital of France?
- @BotName What's the weather in Bangkok?
- @BotName [with image attached] What's in this image?
- !groq "Explain quantum computing simply" model:llama-3.1-8b-versatile
- !vision "What's shown in this picture?" model:llama-3.1-8b-vision
- !weather Tokyo, London, Paris
    """
    await ctx.respond(help_text)

# Run the bot
if __name__ == "__main__":
    bot.run()
