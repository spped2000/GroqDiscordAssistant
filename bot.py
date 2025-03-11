"""
Groq Discord Bot - A Discord bot powered by Groq AI models.

This bot allows users to interact with AI language models through Discord by
mentioning the bot or using commands.
"""
import os
import hikari
import lightbulb
import aiohttp
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv("DISCORD_TOKEN")
BOT_PREFIX = os.getenv("BOT_PREFIX", "!")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama3-70b-8192"
MAX_RESPONSE_LENGTH = 2000

# Constants
MODELS_INFO = """
Available Groq Models:
- llama3-8b-8192: Meta's Llama 3 8B model (fastest)
- llama3-70b-8192: Meta's Llama 3 70B model (more capable, default)
- mixtral-8x7b-32768: Mixtral 8x7B model with 32k context
- gemma-7b-it: Google's Gemma 7B model

Usage:
- Just mention me with your question
- Or use !groq prompt model:<model> for a specific model
"""

HELP_TEXT = """
I'm your helpful AI assistant powered by Groq LLMs!

How to use me:
- Just mention me with your question
- I'll respond to your questions and help with information

Advanced Commands:
- !groq prompt model:<optional_model> - Ask using a specific model
- !models - See available AI models
- !bothelp - Display this help message

Example:
@BotName What's the capital of France?
!groq "Explain quantum computing simply" model:llama3-8b-8192
"""

# Initialize bot
bot = lightbulb.BotApp(token=BOT_TOKEN, prefix=BOT_PREFIX)

# Utility functions
def chunk_message(message: str, chunk_size: int = 2000) -> List[str]:
    """Split a message into chunks that fit within Discord's message length limits."""
    if len(message) <= chunk_size:
        return [message]
        
    chunks = []
    for i in range(0, len(message), chunk_size):
        chunks.append(message[i:i+chunk_size])
    
    return chunks

async def query_groq(prompt: str, model: str = DEFAULT_MODEL) -> Optional[str]:
    """Send a query to the Groq API and return the response."""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
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

# Event listeners
@bot.listen(hikari.GuildMessageCreateEvent)
async def on_message_create(event: hikari.GuildMessageCreateEvent) -> None:
    """Listen to all messages and handle mentions."""
    # Skip messages from bots
    if not event.is_human:
        return
    
    # Skip messages that aren't in guilds
    if not event.message or not event.message.content:
        return
    
    content = event.message.content
    me = bot.get_me()
    
    # Handle mentions
    if me and me.id in event.message.user_mentions_ids:
        # Get the question by removing the mention
        question = content.replace(f"<@{me.id}>", "").strip()
        
        if not question:
            await event.message.respond("Hello! How can I help you today? Ask me any question.")
            return
        
        # Show typing indicator while processing
        await bot.rest.trigger_typing(event.channel_id)
        
        # Get response from Groq
        response = await query_groq(question)
        
        if response:
            # Send response in chunks if needed
            chunks = chunk_message(response, MAX_RESPONSE_LENGTH)
            for chunk in chunks:
                await event.message.respond(chunk)
        else:
            await event.message.respond("I'm sorry, I couldn't process your question right now. Please try again later.")

# Commands
@bot.command
@lightbulb.option("model", "The model to use", required=False, default=DEFAULT_MODEL)
@lightbulb.option("prompt", "Your question or prompt", required=True)
@lightbulb.command("groq", "Ask a question using Groq API")
@lightbulb.implements(lightbulb.PrefixCommand)
async def groq_command(ctx: lightbulb.Context) -> None:
    """Ask a question using the Groq API."""
    # Show typing indicator
    await bot.rest.trigger_typing(ctx.channel_id)
    
    # Get response
    response = await query_groq(ctx.options.prompt, ctx.options.model)
    
    if response:
        # Send in chunks if needed
        chunks = chunk_message(response, MAX_RESPONSE_LENGTH)
        for chunk in chunks:
            await ctx.respond(chunk)
    else:
        await ctx.respond("Sorry, I couldn't get a response from Groq. Please try again later.")

@bot.command
@lightbulb.command("models", "Display available Groq models")
@lightbulb.implements(lightbulb.PrefixCommand)
async def models_command(ctx: lightbulb.Context) -> None:
    """Display information about available Groq models."""
    await ctx.respond(MODELS_INFO)

@bot.command
@lightbulb.command("bothelp", "Display bot usage information")
@lightbulb.implements(lightbulb.PrefixCommand)
async def bothelp_command(ctx: lightbulb.Context) -> None:
    """Display help information about the bot."""
    await ctx.respond(HELP_TEXT)

# Run the bot
if __name__ == "__main__":
    bot.run()