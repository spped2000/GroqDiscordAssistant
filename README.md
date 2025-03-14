# Groq Discord Bot

A Discord bot that uses Groq's API to access powerful AI language models like LLama 3 and Mixtral directly in your Discord server. Now with vision capabilities to analyze images!

## How It Works

```mermaid
flowchart LR
    A[User sends message] --> B{Bot mentioned\nor command used?}
    B -->|No| Z[Ignore]
    B -->|Yes| C[Process input]
    C --> C1{Contains image?}
    C1 -->|No| D1[Send to Groq Text API]
    C1 -->|Yes| D2[Send to Groq Vision API]
    D1 --> E{API response\nsuccessful?}
    D2 --> E
    E -->|No| F[Send error message]
    E -->|Yes| G[Format response]
    G --> H[Send to Discord]
```

## Features

- Ask AI questions by mentioning the bot
- **NEW**: Analyze images by attaching them to your messages (14/3/2025)
- Choose from multiple AI models, including vision models
- Simple command interface
- Handles long responses automatically

## Quick Start

### Requirements

- Python 3.8+
- Discord Bot Token
- Groq API Key

### Installation

1. **Clone or download this repository**
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up environment variables**
   - Copy `.env.example` to `.env`
   - Add your Discord token and Groq API key
4. **Run the bot**
   ```bash
   python bot.py
   ```

## Usage

### Basic Usage

Just mention the bot with your question:
```
@YourBot What's the capital of France?
```

![Bot Usage Example](assets/exp1.png)
*Example: @ตื่นมาโค้ดpython แนะนำอาหารไทยเผ็ดๆหน่อย?*

### Text Chat Examples

#### General Knowledge Queries
You can ask the bot general knowledge questions:
```
@YourBot Who wrote the novel "Pride and Prejudice"?
@YourBot What are the main causes of climate change?
```

#### Using Different Models
Specify a model for different types of responses:
```
!groq "Explain quantum computing in simple terms" model:llama3-70b-8192
!groq "Write a short poem about technology" model:mixtral-8x7b-32768
```

#### Complex Tasks
The bot can handle more complex tasks as well:
```
@YourBot Can you summarize the key differences between machine learning and deep learning?
@YourBot How would you explain the concept of blockchain to a 10-year-old?
```

### NEW: Vision Capabilities

Attach an image and mention the bot with your question about the image:
```
@YourBot [image attached] What's in this image?
```

![Bot Vision Example](assets/exp2.png)

*Example: @ตื่นมาโค้ดpython วัดนี้คือวัดอะไร?*

### Commands

- `!groq <prompt>` - Ask a text question
- `!groq <prompt> model:<model>` - Use a specific text model
- `!vision <prompt>` - Ask about your most recently uploaded image
- `!vision <prompt> model:<model>` - Use a specific vision model
- `!models` - List available models
- `!bothelp` - Show help information

### Available Models

#### Text Models
- `llama3-8b-8192` - Fastest responses
- `llama3-70b-8192` - Most capable (default for text)
- `mixtral-8x7b-32768` - Good for longer contexts
- `gemma-7b-it` - Google's model

#### Vision Models
- `llama-3.2-11b-vision-preview` - Default for images
- `llama-3.2-90b-vision-preview` - More capable vision model

## Vision Examples

### Analyzing Images
The bot can now analyze images and answer questions about them:
- Describe scenes and objects
- Identify text in images
- Answer questions about image content

### Using the Vision Command
If you've already shared an image, you can use the dedicated command:
```
!vision What can you tell me about this image?
```
This will analyze your most recently uploaded image.

## License

MIT License

---

Made with ❤️ using Hikari, Lightbulb, and Groq
