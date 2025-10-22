# Leet Devops - Quick Start Guide

Get up and running with Leet Devops in 5 minutes!

## Prerequisites Checklist

- [ ] Frappe Framework installed
- [ ] A Frappe bench set up
- [ ] Python 3.8 or higher
- [ ] Claude API key from Anthropic

## Step-by-Step Installation

### 1. Get Your Claude API Key (2 minutes)

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Click on "API Keys"
4. Click "Create Key"
5. Copy your API key (starts with `sk-ant-api03-`)

### 2. Install Leet Devops (2 minutes)

```bash
# Navigate to your bench
cd ~/frappe-bench

# Get the app
bench get-app /path/to/leet_devops

# Install on your site (replace 'mysite' with your site name)
bench --site mysite install-app leet_devops

# Install required Python package
bench pip install anthropic

# Restart to apply changes
bench restart
```

### 3. Configure Settings (1 minute)

1. Open your Frappe site in browser
2. Search for "Claude AI Settings" (use Awesome Bar: Ctrl+K)
3. Fill in:
   - **API Key**: Paste your Claude API key
   - **Model**: Keep default (claude-sonnet-4-5-20250929)
   - **Max Tokens**: Keep default (4096)
   - **Temperature**: Keep default (0.7)
   - **Working App Name**: Enter the app you want to work on
4. Click **Save**

## Your First App Generation

### Option A: Create a New App First

```bash
# Create a new Frappe app
bench new-app my_awesome_app

# Install it on your site
bench --site mysite install-app my_awesome_app

# Set it as working app in Claude AI Settings
```

### Option B: Use an Existing App

Just enter the existing app name in Claude AI Settings.

## Start Chatting with Claude

1. Search for "App Generator Chat" (Ctrl+K)
2. Click **New Session**
3. Enter a title: "My First App"
4. Click **Create**

### Try This Example

Type this in the chat:

```
Create a simple Task Management app with:

1. Task DocType with fields:
   - Title (required)
   - Description
   - Status (Select: Open, In Progress, Completed)
   - Priority (Select: Low, Medium, High)
   - Due Date
   - Assigned To (Link to User)

2. Make it simple and clean
```

### What Happens Next

1. Claude will respond with a detailed plan
2. DocType sessions will be created
3. You'll see pending changes in the right sidebar
4. Click **Apply Changes** to create the files
5. Click **Verify Files** to confirm

## Common First-Time Issues

### Issue: "API Key Invalid"

**Solution:**
- Go to Anthropic console and regenerate key
- Make sure you copied the entire key
- Check for extra spaces

### Issue: "App Path Not Found"

**Solution:**
```bash
# Verify your app exists
ls ~/frappe-bench/apps/

# Make sure app name in settings matches exactly
```

### Issue: "Permission Denied"

**Solution:**
```bash
# Give proper permissions
cd ~/frappe-bench/apps/
chmod -R 755 your_app_name
```

## Quick Commands Reference

```bash
# Clear cache if things seem stuck
bench clear-cache

# Migrate to apply changes
bench migrate

# Restart after changes
bench restart

# Check logs for errors
tail -f ~/frappe-bench/logs/frappe.log

# Open Python console for debugging
bench console
```

## Next Steps

Once you've created your first app:

1. **Refine DocTypes**: Click on individual DocTypes to modify them
2. **Add Features**: Ask Claude to add validations, custom scripts
3. **Create More DocTypes**: Keep chatting to expand your app
4. **Test**: Try creating records in your new DocTypes

## Tips for Success

1. **Be Specific**: The more details you give Claude, the better
2. **Iterate**: Start simple, add complexity gradually
3. **Review**: Always check pending changes before applying
4. **Verify**: Use the verify button after applying changes
5. **Learn**: Read the USER_GUIDE.md for advanced usage

## Getting Help

- **Check Logs**: `bench logs`
- **Frappe Docs**: https://frappeframework.com/docs
- **Anthropic Docs**: https://docs.anthropic.com
- **Read USER_GUIDE.md** for detailed usage

## Example Apps to Try

### 1. Simple Blog
```
Create a Blog app with Post and Comment DocTypes
```

### 2. Inventory Tracker
```
Create an Inventory app with Item, Stock Entry, and Warehouse DocTypes
```

### 3. CRM Lite
```
Create a CRM with Lead, Opportunity, and Customer DocTypes
```

### 4. Event Manager
```
Create an Event Management app with Event, Ticket, and Attendee DocTypes
```

## Troubleshooting Checklist

If something doesn't work:

- [ ] API key is correct and active
- [ ] App name matches exactly (case-sensitive)
- [ ] App is installed on site (`bench list-apps`)
- [ ] Bench is running (`bench start`)
- [ ] Cache is cleared (`bench clear-cache`)
- [ ] Migration completed (`bench migrate`)
- [ ] Proper file permissions

## Success Indicators

You'll know it's working when:

✅ Chat messages appear in the interface
✅ Claude responds with detailed suggestions
✅ DocType sessions are created automatically
✅ Pending changes show files to create
✅ Apply changes succeeds without errors
✅ Verify files shows all green checkmarks
✅ Your new DocTypes appear in the system

---

**Congratulations! You're ready to build amazing Frappe apps with AI! 🎉**

For more advanced usage, check out:
- USER_GUIDE.md - Detailed usage instructions
- CONFIG_GUIDE.md - Configuration options
- README.md - Full documentation
