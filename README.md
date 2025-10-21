# Leet DevOps

AI-powered DocType and Function Generator for Frappe Framework

## Overview

Leet DevOps is a Frappe custom app that leverages Claude AI to help developers generate DocTypes, functions, reports, and other artifacts for Frappe applications. It features an intelligent chat interface with session management, automatic child session creation, and streaming responses.

## Features

### 1. **Settings Management**
- Configure Claude API key
- Set token limits and temperature
- Define default target app
- Select AI model (Claude Sonnet 4, Opus 4, etc.)

### 2. **Intelligent Chat Interface**
- Real-time streaming responses from Claude AI
- Context-aware conversations
- Session-based chat history
- Automatic code generation

### 3. **Session Management**
- **Main Sessions**: Overall project planning and discussion
- **Child Sessions**: Automatically created for specific artifacts
  - DocType sessions
  - Function/API sessions
  - Report sessions
  - Page sessions

### 4. **Context Preservation**
- Each session maintains its own context
- Child sessions inherit parent session context
- Automatic embedding of relevant information

### 5. **Artifact Generation**
- Complete DocType generation (JSON, Python, JS)
- API endpoint creation
- Report generation
- Custom page creation
- Proper file structure following Frappe conventions

## Installation

### Prerequisites
- Frappe Framework (v14 or later)
- Python 3.8+
- Anthropic API key

### Steps

1. **Get the app:**
   ```bash
   cd frappe-bench
   bench get-app https://github.com/your-repo/leet_devops.git
   ```

2. **Install on site:**
   ```bash
   bench --site your-site.local install-app leet_devops
   ```

3. **Install Python dependencies:**
   ```bash
   bench pip install anthropic
   ```

4. **Restart bench:**
   ```bash
   bench restart
   ```

## Configuration

1. Navigate to **DevOps Settings** (Settings > DevOps Settings)

2. Configure the following:
   - **Claude API Key**: Your Anthropic API key
   - **Max Tokens**: Maximum tokens per response (default: 4096)
   - **Model**: Select AI model (Claude Sonnet 4.5 recommended)
   - **Temperature**: Response creativity (0-2, default: 1)
   - **Target App Name**: Default Frappe app to generate code for
   - **App Path**: Full path to the target app directory

## Usage

### Creating a New Session

1. Go to **Chat Interface** page
2. Click **"New Session"**
3. Enter:
   - Session title
   - Target app name
   - Session type (Main for overall planning)

### Chatting with Claude

1. Type your request in the chat input
2. Press **Ctrl+Enter** or click **Send**
3. Watch as Claude streams the response in real-time
4. Claude will automatically:
   - Analyze your requirements
   - Create child sessions for specific artifacts
   - Generate complete, production-ready code
   - Provide implementation instructions

### Working with Child Sessions

1. Click **"Child Sessions"** button in the chat header
2. View automatically created child sessions
3. Open specific child sessions to focus on individual artifacts
4. Each child session maintains focused context on its specific task

### Example Workflows

#### Creating a Custom DocType

1. Create a main session: "Customer Portal Development"
2. Ask Claude: "I need a Customer Feedback DocType with fields for rating, comments, and category"
3. Claude will:
   - Create a child session for "Customer Feedback DocType"
   - Generate the JSON definition
   - Create Python controller with validation
   - Add JavaScript for client-side logic
   - Provide installation instructions

#### Building an API

1. In your session, ask: "Create an API to calculate shipping costs based on weight and destination"
2. Claude generates:
   - Complete Python function with @frappe.whitelist()
   - Error handling
   - Documentation
   - Usage examples

## App Structure

```
leet_devops/
├── leet_devops/
│   ├── api/
│   │   └── claude_api.py          # Claude API integration
│   ├── config/
│   │   └── desktop.py             # Workspace configuration
│   ├── leet_devops/               # Main module
│   │   ├── doctype/
│   │   │   ├── devops_settings/   # Settings DocType
│   │   │   ├── generation_session/ # Session management
│   │   │   └── chat_message/      # Chat messages
│   │   └── page/
│   │       └── chat_interface/    # Chat UI
│   └── public/
│       ├── css/
│       │   └── leet_devops.css   # Styles
│       └── js/
│           └── leet_devops.js    # Frontend logic
├── requirements.txt
└── setup.py
```

## DocTypes

### DevOps Settings (Single)
- API configuration
- Model settings
- Default app configuration

### Generation Session
- Session metadata
- Context storage
- Parent-child relationships
- Artifact tracking

### Chat Message
- Message content
- Sender information
- Timestamps
- Token usage tracking

## API Methods

### `claude_api.send_message`
Send a message to Claude with streaming support
- **Args**: session_id, message, stream
- **Returns**: Message ID and content

### `claude_api.create_session`
Create a new generation session
- **Args**: title, target_app, session_type, parent_session
- **Returns**: Session ID

### `claude_api.get_child_sessions`
Get all child sessions for a parent
- **Args**: parent_session_id
- **Returns**: List of child sessions

### `claude_api.get_session_messages`
Get all messages in a session
- **Args**: session_id
- **Returns**: List of messages

## Best Practices

1. **Use Clear Session Titles**: Make them descriptive for easy navigation
2. **Leverage Context**: Claude remembers the conversation within each session
3. **Review Generated Code**: Always review and test generated artifacts
4. **Utilize Child Sessions**: Let Claude automatically organize work into focused sessions
5. **Set Appropriate Token Limits**: Higher limits for complex generations
6. **Monitor API Usage**: Keep track of your Anthropic API usage

## Troubleshooting

### Streaming Not Working
- Check browser console for WebSocket errors
- Ensure Redis is running (required for realtime)
- Verify API key is correct

### No Response from Claude
- Check DevOps Settings has valid API key
- Verify network connectivity
- Check Anthropic API status

### Child Sessions Not Created
- Ensure main session is active
- Check that keywords (doctype, function, etc.) are mentioned
- Review session context

## Development

### Running Tests
```bash
bench --site your-site.local run-tests --app leet_devops
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Security

- API keys are stored encrypted in the database
- Only System Manager role has access by default
- All API calls are logged for audit purposes

## License

MIT License

## Support

For issues and questions:
- GitHub Issues: [Your repo issues page]
- Email: info@leetdevops.com

## Credits

Built with:
- [Frappe Framework](https://frappeframework.com/)
- [Anthropic Claude](https://www.anthropic.com/)

## Version History

### 0.0.1 (Initial Release)
- Basic chat interface
- Session management
- Claude API integration with streaming
- Automatic child session creation
- DevOps Settings configuration
