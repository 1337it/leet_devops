# Configuration Example for Leet Devops

This file shows example configurations for Claude AI Settings.

## Basic Configuration

```
API Key: sk-ant-api03-... (your actual API key)
Model: claude-sonnet-4-5-20250929
Max Tokens: 4096
Temperature: 0.7
Working App Name: my_custom_app
```

## Model Options

### Claude Sonnet 4.5 (Recommended)
- **Model ID**: claude-sonnet-4-5-20250929
- **Best for**: Most tasks, efficient, cost-effective
- **Max Tokens**: Up to 8192
- **Use case**: General app generation, DocType creation

### Claude Opus 4.1
- **Model ID**: claude-opus-4-1-20250514
- **Best for**: Complex reasoning, detailed planning
- **Max Tokens**: Up to 4096
- **Use case**: Complex apps with intricate business logic

### Claude 4
- **Model ID**: claude-4-20250514
- **Best for**: Balanced performance
- **Max Tokens**: Up to 4096
- **Use case**: Standard app generation

## Temperature Settings

**0.0 - 0.3**: More deterministic, consistent
- Best for: Code generation, structured output
- Example: DocType JSON definitions

**0.4 - 0.7**: Balanced creativity and consistency (Recommended)
- Best for: General app development
- Example: Most app generation tasks

**0.8 - 1.0**: More creative, varied responses
- Best for: Brainstorming, design suggestions
- Example: UI/UX ideas, feature suggestions

## Max Tokens Guide

**1024**: Quick responses, simple questions
**2048**: Medium complexity responses
**4096**: Default, handles most tasks well
**8192**: Long, detailed responses (Sonnet 4.5 only)

## Working App Configuration

### New App
```
Working App Name: my_new_app
App Path: /path/to/frappe-bench/apps/my_new_app
```

Before using Leet Devops with a new app, create it first:
```bash
bench new-app my_new_app
bench --site your-site install-app my_new_app
```

### Existing App
```
Working App Name: existing_app
App Path: /path/to/frappe-bench/apps/existing_app
```

The app must already exist in your bench.

## Security Best Practices

1. **Never share your API key**
2. **Use environment variables for sensitive data**
3. **Rotate API keys periodically**
4. **Monitor API usage on Anthropic console**
5. **Restrict access to Claude AI Settings to System Managers only**

## API Usage Tips

1. **Start with lower max_tokens** for cost efficiency
2. **Increase temperature** for more creative suggestions
3. **Use Sonnet 4.5** as default for best balance
4. **Monitor token usage** in your Anthropic dashboard
5. **Set up billing alerts** to avoid surprises

## Troubleshooting Configuration

### API Key Not Working
- Verify the key is correct (starts with sk-ant-api03-)
- Check if key is active in Anthropic console
- Ensure you have sufficient credits
- Try regenerating the key

### App Path Issues
- Ensure the app directory exists
- Check permissions (bench user should have write access)
- Verify the path in settings matches actual path
- Use absolute paths

### Connection Issues
- Check internet connectivity
- Verify firewall settings
- Test API access from terminal:
  ```bash
  curl https://api.anthropic.com/v1/messages \
    -H "x-api-key: YOUR_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -H "content-type: application/json" \
    -d '{"model": "claude-sonnet-4-5-20250929", "max_tokens": 1024, "messages": [{"role": "user", "content": "Hello"}]}'
  ```

## Environment-Specific Settings

### Development
```
Model: claude-sonnet-4-5-20250929
Max Tokens: 4096
Temperature: 0.7
```

### Production
```
Model: claude-sonnet-4-5-20250929
Max Tokens: 2048
Temperature: 0.5
(Use lower tokens to reduce costs)
```

### Testing/Experimentation
```
Model: claude-opus-4-1-20250514
Max Tokens: 8192
Temperature: 0.8
(Higher creativity for exploration)
```

## Cost Optimization

1. **Use appropriate model**: Sonnet for most tasks
2. **Limit max_tokens**: Start with 2048
3. **Be specific in prompts**: Reduces back-and-forth
4. **Use DocType sessions**: More focused conversations
5. **Review before applying**: Avoid regenerating code

## Example Usage Scenarios

### Scenario 1: Simple CRUD App
```
Model: claude-sonnet-4-5-20250929
Max Tokens: 2048
Temperature: 0.5
Estimated tokens per session: 10,000
```

### Scenario 2: Complex Business Logic
```
Model: claude-opus-4-1-20250514
Max Tokens: 4096
Temperature: 0.6
Estimated tokens per session: 30,000
```

### Scenario 3: Quick Modifications
```
Model: claude-sonnet-4-5-20250929
Max Tokens: 1024
Temperature: 0.4
Estimated tokens per session: 3,000
```

---

For more information, visit:
- Anthropic Documentation: https://docs.anthropic.com
- Anthropic Console: https://console.anthropic.com
- Frappe Documentation: https://frappeframework.com
