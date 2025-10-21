# Leet DevOps - Quick Start Guide

Get up and running with Leet DevOps in 5 minutes!

## Prerequisites

- ✅ Frappe Framework installed
- ✅ Anthropic API key ([Get one here](https://console.anthropic.com/))

## Installation (2 minutes)

### Option 1: Using Install Script

```bash
cd frappe-bench
bash /path/to/leet_devops/install.sh
```

Follow the prompts!

### Option 2: Manual Installation

```bash
cd frappe-bench
bench get-app /path/to/leet_devops
bench --site your-site.local install-app leet_devops
bench pip install anthropic
bench restart
```

## Configuration (1 minute)

1. Login to your Frappe site
2. Go to: **Settings → DevOps Settings**
3. Add:
   - **Claude API Key**: `sk-ant-...`
   - **Target App Name**: Your app (e.g., `my_custom_app`)
4. Click **Save**

## First Session (2 minutes)

### Create Your First Session

1. Go to **Chat Interface**
2. Click **"New Session"**
3. Fill in:
   ```
   Title: My First DocType
   Target App: my_custom_app
   Session Type: Main
   ```
4. Click **"Create"**

### Generate Your First DocType

Type this message:

```
Create a simple Task DocType with these fields:
- Title (Data)
- Description (Text Editor)
- Status (Select: Open, In Progress, Completed)
- Due Date (Date)
- Priority (Select: Low, Medium, High)
```

Press **Ctrl+Enter**

### Watch the Magic! ✨

- Claude streams the response
- Complete DocType JSON generated
- Python controller included
- JavaScript client script provided
- Installation instructions given

### Implement the Code

1. Copy the JSON to: `apps/my_custom_app/my_custom_app/my_module/doctype/task/task.json`
2. Copy the Python to: `apps/my_custom_app/my_custom_app/my_module/doctype/task/task.py`
3. Run:
   ```bash
   bench --site your-site.local migrate
   bench restart
   ```
4. Refresh your browser
5. Go to **Task** list - it's there!

## What's Next?

### Try These Commands

**Create an API:**
```
Create an API endpoint to get tasks by status with filters
```

**Generate a Report:**
```
Build a Task Summary Report showing:
- Tasks by priority
- Tasks by status
- Overdue tasks
Include date range filters
```

**Make a Dashboard:**
```
Create a Task Dashboard page with:
- Task statistics
- Priority breakdown chart
- Recent tasks list
```

### Explore Features

1. **Child Sessions**: Claude automatically creates focused sessions
2. **Context Preservation**: Continue conversations naturally
3. **Code Review**: Ask Claude to review and improve your code
4. **Best Practices**: Get Frappe framework guidance

## Common Commands

### Generate DocType
```
Create a [Name] DocType with [fields]
```

### Generate Function
```
Write a function to [do something]
```

### Generate Report
```
Build a report showing [data] with [filters]
```

### Review Code
```
Review this code:
[paste your code]
```

## Tips for Better Results

1. **Be Specific**: More details = better code
2. **Use Context**: Reference previous messages
3. **Iterate**: Refine in multiple messages
4. **Test**: Always test generated code
5. **Customize**: Modify to fit your needs

## Example Session Flow

```
You: I'm building an inventory management system

Claude: I'll help you create a comprehensive inventory system...

You: Start with a Product DocType

Claude: [Generates Product DocType]
       [Creates child session automatically]

You: Now add a Stock Movement DocType

Claude: [Generates Stock Movement DocType]
       [Creates another child session]

You: Create a function to check available stock

Claude: [Generates stock check function]
       [Adds to Functions child session]
```

## Keyboard Shortcuts

- **Ctrl+Enter**: Send message
- **Refresh**: Reload messages

## Troubleshooting

### No Response?
- Check API key in settings
- Verify internet connection
- Check Anthropic console

### Code Not Working?
- Copy exactly as provided
- Check file paths
- Run `bench migrate`
- Clear cache: `bench clear-cache`

### Can't Find Chat Interface?
- URL: `http://your-site.local/app/chat-interface`
- Or search "Chat Interface" in desk

## Need Help?

- 📖 Read: [User Guide](USER_GUIDE.md)
- 🔧 Check: [Installation Guide](INSTALLATION_GUIDE.md)
- 💡 Examples: [Examples](EXAMPLES.md)
- 🐛 Report: [GitHub Issues](https://github.com/your-repo/issues)

## Pro Tips

### Batch Generation
```
Generate these 5 DocTypes:
1. Customer
2. Product
3. Order
4. Order Item
5. Payment

Link them with appropriate relationships
```

### Complex Workflows
```
Create an approval workflow for Leave Applications:
- Employee submits
- Manager approves/rejects
- HR finalizes
- Auto-email notifications
```

### Integration
```
Create an API to integrate with [service]
Include authentication and error handling
```

## Success! 🎉

You're now ready to supercharge your Frappe development with AI!

Start simple, experiment, and let Claude help you build amazing things.

---

**Remember**: Claude is your AI pair programmer. Treat it like a knowledgeable colleague - explain your needs, ask questions, iterate together!
