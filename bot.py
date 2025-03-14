import hikari
import lightbulb
import aiohttp
import base64
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

bot = lightbulb.BotApp(
    token=os.getenv("DISCORD_API_KEY"),
    prefix="!"
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.3-70b-versatile"
DEFAULT_VISION_MODEL = "llama-3.2-11b-vision-preview"

async def fetch_image(url: str) -> Optional[bytes]:
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
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    messages = []
    
    if image_urls and ("vision" in model):
        message_content: List[Dict[str, Any]] = []
        message_content.append({"type": "text", "text": prompt})
        
        for url in image_urls:
            image_data = await fetch_image(url)
            if image_data:
                base64_image = base64.b64encode(image_data).decode('utf-8')
                message_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                })
        
        messages.append({"role": "user", "content": message_content})
    else:
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
    if not event.is_human:
        return
    
    if not event.message or not event.message.content:
        return
    
    content = event.message.content
    me = bot.get_me()
    
    if me and me.id in event.message.user_mentions_ids:
        question = content.replace(f"<@{me.id}>", "").strip()
        
        if not question:
            await event.message.respond("Hello! How can I help you today? Ask me any question.")
            return
        
        await bot.rest.trigger_typing(event.channel_id)
        
        image_urls = []
        if event.message.attachments:
            for attachment in event.message.attachments:
                if attachment.media_type and attachment.media_type.startswith('image/'):
                    image_urls.append(attachment.url)
        
        model = DEFAULT_VISION_MODEL if image_urls else DEFAULT_MODEL
        
        response = await query_groq(question, model, image_urls)
        
        if response:
            if len(response) > 2000:
                chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                for chunk in chunks:
                    await event.message.respond(chunk)
            else:
                await event.message.respond(response)
        else:
            await event.message.respond("I'm sorry, I couldn't process your question right now. Please try again later.")

@bot.command
@lightbulb.option("model", "The model to use", required=False, default=DEFAULT_MODEL)
@lightbulb.option("prompt", "Your question or prompt", required=True)
@lightbulb.command("groq", "Ask a question using Groq API")
@lightbulb.implements(lightbulb.PrefixCommand)
async def groq_command(ctx: lightbulb.Context) -> None:
    await bot.rest.trigger_typing(ctx.channel_id)
    
    response = await query_groq(ctx.options.prompt, ctx.options.model)
    
    if response:
        if len(response) > 2000:
            chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
            for chunk in chunks:
                await ctx.respond(chunk)
        else:
            await ctx.respond(response)
    else:
        await ctx.respond("Sorry, I couldn't get a response from Groq. Please try again later.")

@bot.command
@lightbulb.option("model", "The vision model to use", required=False, default=DEFAULT_VISION_MODEL)
@lightbulb.option("prompt", "Your question about the image", required=True)
@lightbulb.command("vision", "Ask a question about the last image you uploaded")
@lightbulb.implements(lightbulb.PrefixCommand)
async def vision_command(ctx: lightbulb.Context) -> None:
    await bot.rest.trigger_typing(ctx.channel_id)
    
    channel = await bot.rest.fetch_channel(ctx.channel_id)
    messages = await bot.rest.fetch_messages(channel.id, limit=10)
    
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
    
    response = await query_groq(ctx.options.prompt, ctx.options.model, image_urls)
    
    if response:
        if len(response) > 2000:
            chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
            for chunk in chunks:
                await ctx.respond(chunk)
        else:
            await ctx.respond(response)
    else:
        await ctx.respond("Sorry, I couldn't get a response from Groq. Please try again later.")

@bot.command
@lightbulb.command("models", "Display available Groq models")
@lightbulb.implements(lightbulb.PrefixCommand)
async def models_command(ctx: lightbulb.Context) -> None:
    models_info = """
Available Groq Models:

Text Models:
- llama3-8b-8192: Meta's Llama 3 8B model (fastest)
- llama3-70b-8192: Meta's Llama 3 70B model (more capable, default for text)
- mixtral-8x7b-32768: Mixtral 8x7B model with 32k context
- gemma-7b-it: Google's Gemma 7B model

Vision Models:
- llama-3.2-11b-vision-preview: Llama 3.2 11B vision model (default for images)
- llama-3.2-90b-vision-preview: Llama 3.2 90B vision model (more capable)

Usage:
- Just mention me with your question (with or without attached images)
- Use !groq prompt model:<model> for text-only queries
- Use !vision prompt model:<model> for image queries (uses your most recent image)
    """
    await ctx.respond(models_info)

@bot.command
@lightbulb.command("bothelp", "Display bot usage information")
@lightbulb.implements(lightbulb.PrefixCommand)
async def bothelp_command(ctx: lightbulb.Context) -> None:
    help_text = """
I'm your helpful AI assistant powered by Groq LLMs!

How to use me:
- Just mention me (@VIDIOS) with your question
- I'll respond to your questions and help with information
- You can also attach images and ask me about them!

Advanced Commands:
- !groq prompt model:<optional_model> - Ask using a specific text model
- !vision prompt model:<optional_model> - Ask about your most recently posted image
- !models - See available AI models
- !bothelp - Display this help message

Examples:
- @VIDIOS What's the capital of France?
- @VIDIOS [with image attached] What's in this image?
- !groq "Explain quantum computing simply" model:llama3-8b-8192
- !vision "What's shown in this picture?" model:llama-3.2-90b-vision-preview
    """
    await ctx.respond(help_text)

if __name__ == "__main__":
    bot.run()
