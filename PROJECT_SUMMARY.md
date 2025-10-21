# Leet DevOps - Project Summary

## Overview

**Leet DevOps** is a comprehensive Frappe custom app that integrates Claude AI to revolutionize Frappe development. It provides an intelligent chat interface for generating DocTypes, functions, reports, and other Frappe artifacts with streaming responses and automatic session management.

## Key Features

### 1. AI-Powered Code Generation
- Generate complete DocTypes (JSON, Python, JS)
- Create API endpoints and functions
- Build custom reports
- Design custom pages
- Following Frappe best practices

### 2. Intelligent Session Management
- **Main Sessions**: Project planning and coordination
- **Child Sessions**: Automatically created for specific artifacts
- Context preservation across sessions
- Parent-child session relationships

### 3. Real-Time Streaming Interface
- Live streaming responses from Claude
- WebSocket-based real-time updates
- Professional chat UI with message history
- Keyboard shortcuts for efficiency

### 4. Comprehensive Settings
- API key management (encrypted)
- Token limits configuration
- Model selection (Claude Sonnet 4.5, Opus 4)
- Temperature control
- Default app configuration

## Technical Architecture

### DocTypes

#### 1. DevOps Settings (Single)
**Purpose**: App configuration
**Fields**:
- claude_api_key (Password, encrypted)
- max_tokens (Int)
- model (Select)
- temperature (Float)
- target_app_name (Data)
- app_path (Data)

#### 2. Generation Session
**Purpose**: Session management
**Fields**:
- title (Data)
- target_app (Data)
- status (Select: Active/Completed/Archived)
- session_type (Select: Main/DocType/Function/Report/Page)
- parent_session (Link)
- session_context (Long Text)
- artifacts_generated (Long Text)

**Naming**: Auto-generated hash

#### 3. Chat Message
**Purpose**: Message storage
**Fields**:
- session (Link to Generation Session)
- message_type (Select: User/Assistant/System)
- sender (Data)
- timestamp (Datetime)
- message_content (Long Text)
- token_count (Int)
- model_used (Data)

**Naming**: Format: MSG-{session}-{####}

### API Endpoints

#### `/api/method/leet_devops.api.claude_api.send_message`
Send message to Claude with streaming support

**Parameters**:
- session_id: str
- message: str
- stream: bool (default: True)

**Returns**: 
```json
{
  "success": true,
  "message_id": "MSG-xxx-0001",
  "content": "Response text" // if not streaming
}
```

#### `/api/method/leet_devops.api.claude_api.create_session`
Create new generation session

**Parameters**:
- title: str
- target_app: str
- session_type: str (default: "Main")
- parent_session: str (optional)

**Returns**: Session ID

#### `/api/method/leet_devops.api.claude_api.get_child_sessions`
Get all child sessions

**Parameters**:
- parent_session_id: str

**Returns**: List of child sessions

#### `/api/method/leet_devops.api.claude_api.get_session_messages`
Get all messages in a session

**Parameters**:
- session_id: str

**Returns**: List of messages

### Frontend Components

#### Chat Interface Page (`chat-interface`)
**Location**: `/app/chat-interface`

**Features**:
- Create new sessions
- View recent sessions
- Open existing sessions
- Settings access

#### Chat Interface Class (`leet_devops.ChatInterface`)
**File**: `public/js/leet_devops.js`

**Methods**:
- `send_message()`: Send user message
- `create_streaming_placeholder()`: Show typing indicator
- `append_streaming_content()`: Update streaming content
- `finalize_message()`: Complete message rendering
- `show_child_sessions()`: Display child sessions dialog
- `load_messages()`: Load conversation history

### Streaming Architecture

**Flow**:
1. User sends message → API creates user message record
2. API calls Anthropic with streaming enabled
3. As chunks arrive → Published via `frappe.publish_realtime`
4. Frontend listens via WebSocket → Updates UI in real-time
5. On completion → Message saved, child sessions analyzed

**Event**: `claude_response`

**Payload**:
```javascript
{
  session_id: "GEN-0001",
  message_id: "MSG-xxx-0001",
  content: "chunk or full text",
  done: boolean
}
```

### Automatic Child Session Creation

**Trigger Keywords**:
- DocType: "doctype", "document type", "create doctype"
- Function: "function", "api endpoint", "method"
- Report: "report", "create report"
- Page: "page", "custom page"

**Process**:
1. Claude response analyzed for keywords
2. If main session + keywords found → Create child session
3. Child session inherits parent context
4. User can continue work in focused child session

## File Structure

```
leet_devops/
├── leet_devops/                    # Main app directory
│   ├── __init__.py                 # Version info
│   ├── hooks.py                    # Frappe hooks
│   ├── modules.txt                 # Module list
│   ├── patches.txt                 # DB migrations
│   │
│   ├── api/                        # API endpoints
│   │   ├── __init__.py
│   │   └── claude_api.py           # Claude integration
│   │
│   ├── config/                     # Configuration
│   │   ├── __init__.py
│   │   └── desktop.py              # Workspace config
│   │
│   ├── leet_devops/                # Main module
│   │   ├── __init__.py
│   │   ├── doctype/                # DocTypes
│   │   │   ├── devops_settings/
│   │   │   ├── generation_session/
│   │   │   └── chat_message/
│   │   └── page/                   # Pages
│   │       └── chat_interface/
│   │
│   ├── public/                     # Static assets
│   │   ├── css/
│   │   │   └── leet_devops.css
│   │   └── js/
│   │       └── leet_devops.js
│   │
│   ├── templates/                  # Templates
│   │   └── __init__.py
│   │
│   └── translations/               # i18n files
│
├── requirements.txt                # Python dependencies
├── setup.py                        # Installation config
├── license.txt                     # MIT License
├── .gitignore                      # Git ignore rules
├── MANIFEST.in                     # Package manifest
│
├── README.md                       # Project overview
├── INSTALLATION_GUIDE.md           # Installation steps
├── USER_GUIDE.md                   # User documentation
├── QUICKSTART.md                   # Quick start guide
├── PROJECT_SUMMARY.md              # This file
└── install.sh                      # Installation script
```

## Dependencies

### Python
- frappe (Frappe Framework)
- anthropic>=0.18.0 (Claude AI SDK)

### System
- Redis (for real-time features)
- SocketIO (for WebSocket support)

## Security Features

1. **API Key Encryption**: Stored as Password field (encrypted in DB)
2. **Role-Based Access**: Default to System Manager only
3. **Input Validation**: All user inputs validated
4. **Error Handling**: Comprehensive error handling and logging
5. **Audit Trail**: All messages logged with timestamps

## Performance Considerations

1. **Streaming**: Reduces perceived latency
2. **Lazy Loading**: Messages loaded on demand
3. **Efficient Queries**: Optimized database queries
4. **Caching**: Session context cached appropriately
5. **Rate Limiting**: Configurable token limits

## Best Practices Implemented

### Code Quality
- Type hints where applicable
- Comprehensive docstrings
- Error handling with proper logging
- Clean, maintainable code structure

### Frappe Conventions
- Standard naming conventions
- Proper use of hooks
- Following DocType patterns
- Client-server separation

### User Experience
- Responsive design
- Real-time feedback
- Clear error messages
- Intuitive navigation
- Keyboard shortcuts

## Extension Points

### Custom Skills
The system prompt can be extended with domain-specific knowledge:

```python
def prepare_system_prompt(session):
    base_prompt = "..."
    
    # Add custom domain knowledge
    if session.target_app == "healthcare":
        base_prompt += "\nHealthcare-specific guidelines..."
    
    return base_prompt
```

### Custom Analyzers
Add specialized artifact detection:

```python
def analyze_healthcare_artifacts(response_content):
    # Custom logic for healthcare DocTypes
    pass
```

### Workflow Integration
Integrate with Frappe workflows:

```python
doc_events = {
    "Generation Session": {
        "on_submit": "auto_implement_code"
    }
}
```

## Future Enhancements

### Planned Features
1. **Code Implementation**: Auto-implement generated code
2. **Testing**: Generate unit tests
3. **Documentation**: Auto-generate docs
4. **Version Control**: Git integration
5. **Templates**: Reusable artifact templates
6. **Collaboration**: Multi-user sessions
7. **Analytics**: Usage tracking and insights

### Potential Integrations
- GitHub/GitLab for version control
- Slack/Discord for notifications
- Jira/Linear for task tracking
- VS Code extension

## Testing Strategy

### Unit Tests
- DocType validation
- API endpoint testing
- Message handling
- Session management

### Integration Tests
- Claude API integration
- Streaming functionality
- Child session creation
- Context preservation

### Manual Testing
- UI/UX testing
- Performance testing
- Security testing
- Cross-browser testing

## Deployment

### Development
```bash
bench get-app leet_devops
bench --site dev.local install-app leet_devops
bench start
```

### Production
```bash
bench get-app leet_devops
bench --site production.com install-app leet_devops
bench --site production.com migrate
bench build --app leet_devops
sudo supervisorctl restart all
```

## Monitoring

### Key Metrics
- API usage (tokens consumed)
- Response times
- Error rates
- Session creation rate
- User engagement

### Logging
- API calls logged
- Errors with full traceback
- User actions audited
- Performance metrics

## Support & Community

### Documentation
- Complete installation guide
- Comprehensive user guide
- Quick start tutorial
- API documentation

### Community
- GitHub Discussions
- Issue tracking
- Feature requests
- Contribution guidelines

## License

MIT License - Free for commercial and personal use

## Credits

- **Framework**: Frappe Framework
- **AI**: Anthropic Claude
- **Contributors**: [List contributors]

## Version History

### v0.0.1 (Initial Release)
- Core chat interface
- Session management
- Claude API integration
- Streaming support
- Child session automation
- Settings management

## Contact

- **Email**: info@leetdevops.com
- **GitHub**: github.com/your-repo/leet_devops
- **Website**: [Your website]

---

**Built with ❤️ for the Frappe Community**
