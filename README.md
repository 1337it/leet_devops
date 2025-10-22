# Leet Devops

AI-powered Frappe app generator using Claude API. Create and modify Frappe applications through natural conversation with Claude AI.

## Features

- **AI-Powered Development**: Chat with Claude AI to design and develop Frappe apps
- **Session Management**: Organize development work in sessions with conversation history
- **DocType-Specific Chats**: Each DocType gets its own chat session with context-aware conversations
- **Automated File Operations**: Automatically creates DocType files (JSON, Python) in the correct structure
- **Change Preview**: See exactly what files will be created/modified before applying
- **File Verification**: Verify that all expected files were created successfully
- **Automatic Migration**: Runs `bench migrate` automatically after applying changes

## Installation

1. Navigate to your Frappe bench directory:
```bash
cd /path/to/frappe-bench
```

2. Get the app from the repository (or copy the app folder):
```bash
bench get-app /path/to/leet_devops
```

3. Install the app on your site:
```bash
bench --site your-site install-app leet_devops
```

4. Restart bench:
```bash
bench restart
```

## Configuration

1. Navigate to **Leet Devops > Settings > Claude API Settings**

2. Configure the following:
   - **Claude API Key**: Your Anthropic API key (required)
   - **API Endpoint**: Default is `https://api.anthropic.com/v1/messages`
   - **Model**: Choose from Claude Sonnet 4.5, Opus 4.1, or Claude 4
   - **Max Tokens**: Maximum tokens per response (default: 4096)
   - **Temperature**: Controls randomness (default: 0.7)
   - **Default App Name**: Your app name (e.g., `my_custom_app`)
   - **Apps Path**: Full path to your Frappe apps directory (e.g., `/home/frappe/frappe-bench/apps`)

3. Save the settings.

## Usage

### Starting a New Development Session

1. Go to **Leet Devops > Development > App Development Session**
2. Click **New**
3. Fill in:
   - **App Name**: Name of your Frappe app (snake_case)
   - **App Title**: Display title (optional)
   - **Description**: Brief description of what your app does
4. Save the session

### Chatting with Claude AI

1. Open your session
2. Click on the session name to access the **App Development Chat** interface
3. You'll see:
   - Session information at the top
   - Tabs for Main App and each DocType
   - Chat interface
   - Action buttons

### Main App Chat

When on the "Main App" tab, you can:
- Discuss app architecture and design
- Ask Claude to create new DocTypes
- Get suggestions for app structure
- Request explanations of Frappe concepts

Example prompts:
```
"Create a Customer Management DocType with fields for name, email, phone, and address"

"I need a task tracking system with DocTypes for Projects, Tasks, and Time Logs"

"Explain how to create a relationship between two DocTypes"
```

### DocType-Specific Chat

Once Claude creates a DocType definition:
1. A new tab appears for that DocType
2. Click the tab to enter DocType-specific chat
3. The conversation is now focused on that specific DocType

Example prompts in DocType chat:
```
"Add a field for customer rating from 1-5"

"Make the email field mandatory"

"Add a link field to connect this to the Project DocType"

"Change the status field options to include 'Pending', 'In Progress', 'Completed'"
```

### Applying Changes

1. After Claude provides DocType definitions, click **Apply Changes**
2. Review the changes that will be made
3. Confirm to proceed
4. The app will:
   - Create necessary directories
   - Generate JSON and Python files for each DocType
   - Run `bench migrate` automatically
   - Log all file operations

### Verifying Files

1. Click **Verify Files** to check if all expected files were created
2. View the verification results showing:
   - Which files exist
   - File sizes
   - Any missing files

## Workflow Example

Here's a complete workflow example:

1. **Create Session**
   - Name: `library_management`
   - Description: "A library management system"

2. **Main Chat - Design the App**
   ```
   User: "Create a library management system with DocTypes for Books, Members, and Transactions"
   
   Claude: [Provides architectural overview and creates Book DocType definition]
   ```

3. **Switch to Book DocType Tab**
   ```
   User: "Add fields for ISBN, author, publisher, and publication year"
   
   Claude: [Provides updated DocType with new fields]
   ```

4. **Apply Changes**
   - Click "Apply Changes"
   - Files are created automatically
   - Migration runs

5. **Verify**
   - Click "Verify Files"
   - Confirm all files were created successfully

6. **Continue Development**
   - Switch to other DocType tabs or main chat
   - Request modifications
   - Apply and verify again

## File Structure

The app creates the following structure:

```
your_app/
└── your_app/
    ├── hooks.py
    ├── __init__.py
    └── doctype/
        └── your_doctype/
            ├── your_doctype.json
            ├── your_doctype.py
            └── __init__.py
```

## Features in Detail

### Session Management
- **Conversation History**: All conversations are saved per session
- **Multiple Sessions**: Work on different apps simultaneously
- **Status Tracking**: Monitor session status (Active, Pending Changes, Completed, Error)

### DocType Sessions
- **Isolated Context**: Each DocType has its own conversation thread
- **Definition Storage**: DocType JSON is stored in the session
- **Status Tracking**: Track which DocTypes are Draft, Ready, or Applied

### File Operations
- **Automatic Directory Creation**: Creates proper Frappe directory structure
- **JSON Generation**: Creates DocType JSON with proper formatting
- **Python Controller**: Generates basic Python controller classes
- **Init Files**: Creates required __init__.py files
- **Change Logging**: All file operations are logged in File Change Log

### Safety Features
- **Preview Before Apply**: See what will change before applying
- **Confirmation Dialogs**: Confirm before making file system changes
- **Error Handling**: Graceful error handling with detailed messages
- **Verification System**: Verify files after creation

## API Methods

Available whitelisted methods:

- `send_message_to_claude`: Send messages to Claude API
- `parse_doctype_from_response`: Extract DocType JSON from responses
- `create_doctype_session`: Create new DocType session
- `apply_changes`: Apply pending changes to file system
- `verify_files`: Verify file creation
- `run_migrate`: Run bench migrate
- `get_app_list`: Get list of installed apps

## Limitations

- Requires valid Claude API key
- File operations require proper permissions on apps directory
- bench commands must be available in the system path
- Currently supports DocType creation only (pages, reports, etc. coming soon)

## Troubleshooting

### API Key Issues
- Verify your Claude API key in settings
- Check API key has proper permissions
- Ensure you have API credits available

### File Creation Issues
- Verify Apps Path is correct in settings
- Check directory permissions
- Ensure the target app directory exists

### Migration Issues
- Check bench is installed and accessible
- Verify you're in the correct environment
- Check error logs in File Change Log

## Future Enhancements

- Support for creating Pages
- Support for creating Reports
- Support for Web Forms
- Code file modifications (not just DocTypes)
- Client Script generation
- Server Script integration
- Workflow creation
- Print Format generation

## License

MIT

## Credits

Developed using:
- Frappe Framework
- Claude API by Anthropic
- Python 3.6+

## Support

For issues and questions:
1. Check the File Change Log for error details
2. Review conversation history in sessions
3. Verify configuration in Claude API Settings

---

Built with ❤️ for the Frappe community
