# Groq Discord Bot

A powerful Discord bot that integrates Groq's language models into your Discord server, allowing users to interact with state-of-the-art AI directly through chat commands and mentions.

![Discord Bot Flow](https://via.placeholder.com/800x400?text=Groq+Discord+Bot)

## 📚 Overview

Groq Discord Bot is designed to bring advanced AI capabilities to Discord by leveraging Groq's fast inference API. With this bot, server members can:

- Ask questions and get AI-powered responses by simply mentioning the bot
- Choose from multiple language models with different capabilities
- Use various commands to interact with the models in different ways

The bot handles all the complexity of API communication and response formatting, delivering a seamless experience for users.

## ✨ Features

- **Simple Mention Interface**: Just mention the bot with your question to get a response
- **Multiple AI Models**: Choose from models like LLama 3, Mixtral, and Gemma
- **Prefix Commands**: Use commands like `!groq` to interact with specific models
- **Smart Response Handling**: Automatically splits long responses into multiple messages
- **Comprehensive Help**: Built-in help commands to guide users
- **Modular Structure**: Easy to extend with new features
- **Robust Error Handling**: Gracefully handles API errors and limitations

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- A Discord Bot Token ([Discord Developer Portal](https://discord.com/developers/applications))
- A Groq API Key ([Groq Website](https://console.groq.com/))

### Step 1: Clone the repository

```bash
git clone https://github.com/yourusername/groq-discord-bot.git
cd groq-discord-bot
```

### Step 2: Set up a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure environment variables

Create a `.env` file in the root directory based on the `.env.example` template:

```bash
cp .env.example .env
```

Edit the `.env` file with your credentials:

```
# Discord Bot Configuration
DISCORD_TOKEN=your_discord_token_here
BOT_PREFIX=!

# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here
DEFAULT_MODEL=llama3-70b-8192
```

## 🚀 Usage

### Starting the Bot

Run the bot with:

```bash
python -m bot.main
```

Or if you've installed the package:

```bash
groq-bot
```

### Interacting with the Bot

#### Mention the Bot

The simplest way to interact with the bot is to mention it followed by your question:

```
@VIDIOS What is the capital of Japan?
```

The bot will process your question and respond with an answer.

#### Commands

The bot supports several commands (using the default `!` prefix):

- `!groq <prompt> model:<model_name>` - Send a prompt to a specific model
- `!models` - Show a list of available AI models
- `!bothelp` - Display help information

Examples:

```
!groq Explain quantum computing in simple terms
!groq Tell me about the solar system model:llama3-8b-8192
```

### Available Models

The bot supports the following Groq models:

| Model | Description | Best For |
|-------|-------------|----------|
| llama3-8b-8192 | Meta's Llama 3 (8B parameters) | Quick responses, simple queries |
| llama3-70b-8192 | Meta's Llama 3 (70B parameters) | Detailed responses, complex reasoning |
| mixtral-8x7b-32768 | Mixtral model with 32k context | Long-context understanding |
| gemma-7b-it | Google's Gemma model | General-purpose tasks |

## 🧩 Project Structure

```
groq-discord-bot/
├── bot/
│   ├── __init__.py
│   ├── config.py              # Configuration settings
│   ├── main.py                # Entry point
│   ├── cogs/                  # Command modules
│   │   ├── __init__.py
│   │   ├── general.py         # General commands
│   │   └── groq_commands.py   # Groq-specific commands
│   ├── services/              # Business logic
│   │   ├── __init__.py
│   │   └── groq_service.py    # Groq API interaction
│   └── utils/                 # Utility functions
│       ├── __init__.py
│       ├── constants.py       # Constant values
│       └── message_utils.py   # Message handling
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── test_groq_service.py
│   └── test_commands.py
├── .env.example               # Example environment variables
├── .gitignore                 # Git ignore file
├── LICENSE                    # License information
├── README.md                  # This documentation
├── requirements.txt           # Dependencies
└── setup.py                   # Installation script
```

## 🔍 Technical Details

### How It Works

The bot operates with these main components:

1. **Event Listeners**: Detect when users mention the bot or use commands
2. **Command Handlers**: Process command arguments and options
3. **Groq Service**: Communicates with the Groq API to generate responses
4. **Message Utilities**: Format and chunk responses for Discord's constraints

### Flow Diagram

```
User Message → Bot Processes Command → Query Sent to Groq API → 
Response Processed → Formatted Response Sent to Discord
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 Testing

Run the test suite with:

```bash
pytest
```

The project includes unit tests for core functionality including:
- API communication
- Command processing
- Response formatting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

- **Bot not responding to commands**: Make sure the bot has proper permissions in your Discord server
- **API errors**: Check your Groq API key and model availability
- **Missing environment variables**: Ensure your `.env` file is properly set up

### Getting Help

If you encounter issues not covered here, please open an issue on GitHub.

## 🙏 Acknowledgements

- [Hikari](https://github.com/hikari-py/hikari) - Discord API wrapper
- [Lightbulb](https://github.com/tandemdude/hikari-lightbulb) - Command framework
- [Groq](https://groq.com/) - AI model provider
- [python-dotenv](https://github.com/theskumar/python-dotenv) - Environment variable management

---

Developed with ❤️ for the Discord community
