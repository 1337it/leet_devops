# Leet Devops - Installation & Quick Start Guide

## Prerequisites

1. **Frappe Framework** installed and running
2. **Frappe Bench** set up
3. **Claude API Key** from Anthropic (https://console.anthropic.com/)
4. **Python 3.6+**
5. **System access** to apps directory with write permissions

## Step-by-Step Installation

### 1. Get the App

Navigate to your Frappe bench directory:
```bash
cd /path/to/frappe-bench
```

Copy the leet_devops folder to your apps directory:
```bash
cp -r /path/to/leet_devops apps/
```

Or clone from repository:
```bash
bench get-app https://github.com/yourusername/leet_devops.git
```

### 2. Install the App

Install on your site:
```bash
bench --site your-site-name install-app leet_devops
```

### 3. Migrate Database

```bash
bench --site your-site-name migrate
```

### 4. Restart Services

```bash
bench restart
```

### 5. Clear Cache

```bash
bench --site your-site-name clear-cache
```

## Initial Configuration

### 1. Access Claude API Settings

1. Login to your Frappe site
2. Go to **Awesome Bar** (Ctrl/Cmd + K)
3. Type "Claude API Settings" and open it

### 2. Configure API Key

```
Claude API Key: sk-ant-api03-xxxxx... (your Anthropic API key)
API Endpoint: https://api.anthropic.com/v1/messages (default)
Model: claude-sonnet-4-5-20250929 (or choose another model)
Max Tokens: 4096
Temperature: 0.7
```

### 3. Configure App Settings

```
Default App Name: my_app (name of your app to develop)
Apps Path: /home/frappe/frappe-bench/apps (full path to apps directory)
```

**Important**: The Apps Path must be the absolute path to your Frappe bench apps directory where all apps are stored.

### 4. Save Settings

Click **Save**. You're now ready to start developing!

## Quick Start - Create Your First App

### Step 1: Create App Structure

First, create a basic Frappe app structure manually or using bench:

```bash
bench new-app my_custom_app
```

Fill in the details when prompted. This creates the base app structure.

### Step 2: Install the New App

```bash
bench --site your-site-name install-app my_custom_app
```

### Step 3: Create Development Session

1. Go to **Leet Devops > App Development Session**
2. Click **New**
3. Fill in:
   - **App Name**: `my_custom_app` (same as your app)
   - **App Title**: My Custom App
   - **Description**: A custom app for managing customers
4. Click **Save**

### Step 4: Open Chat Interface

1. Click on the session name
2. You'll be redirected to the chat interface at `/app_chat?session=APP-DEV-00001`

### Step 5: Start Chatting with Claude

In the chat interface, try these prompts:

**Example 1: Create a Simple DocType**
```
Create a Customer DocType with the following fields:
- Customer Name (required)
- Email (required)
- Phone
- Address
- Status (Draft, Active, Inactive)
```

**Example 2: Create Multiple Related DocTypes**
```
I need a project management system with:
1. Projects DocType (name, description, start date, end date, status)
2. Tasks DocType (task name, project link, assigned to, due date, status)
3. Time Logs DocType (task link, hours, date, description)
```

### Step 6: Review Claude's Response

Claude will provide:
- Explanation of the DocTypes
- Complete JSON definitions
- Suggestions for improvements

### Step 7: Create DocType Sessions

When Claude provides a DocType definition:
1. The system will ask if you want to create a session for it
2. Click **Yes** to create a DocType-specific session
3. A new tab will appear for that DocType

### Step 8: Refine DocTypes

Click on a DocType tab to chat specifically about that DocType:

```
Add a field for customer rating from 1 to 5

Make the email field mandatory and add email validation

Add a currency field for customer credit limit
```

### Step 9: Apply Changes

1. Click **Apply Changes** button
2. Review the files that will be created
3. Click **OK** to confirm
4. The system will:
   - Create directory structure
   - Generate JSON and Python files
   - Run `bench migrate`
   - Show results

### Step 10: Verify Files

1. Click **Verify Files** button
2. Review verification results
3. Check that all expected files exist

### Step 11: Test Your DocTypes

1. Go to your site
2. Search for your new DocTypes in the Awesome Bar
3. Create test records
4. Verify everything works correctly

## Example Session Flow

Here's a complete example of developing a simple CRM:

### Initial Chat (Main App Tab)
```
User: "Create a simple CRM with Customer and Lead DocTypes"

Claude: [Provides overview and creates Customer DocType definition]

System: "DocType definition found for Customer. Create session?"
User: Clicks Yes

Claude: [Creates Lead DocType definition]

System: "DocType definition found for Lead. Create session?"
User: Clicks Yes
```

### Customer DocType Tab
```
User: "Add these fields: customer_name, email, phone, company, industry, status"

Claude: [Provides updated Customer DocType JSON]

User: "Make email and customer_name required"

Claude: [Updates JSON with required fields]

User: "Add a link field to connect to Lead DocType"

Claude: [Adds link field]
```

### Lead DocType Tab
```
User: "Add fields: lead_name, email, phone, source, status, notes"

Claude: [Provides updated Lead DocType JSON]

User: "Add a button to convert lead to customer"

Claude: [Explains how to add custom button - implementation would need custom code]
```

### Apply and Verify
```
1. Click "Apply Changes"
2. System creates:
   - my_custom_app/my_custom_app/doctype/customer/
     - customer.json
     - customer.py
     - __init__.py
   - my_custom_app/my_custom_app/doctype/lead/
     - lead.json
     - lead.py
     - __init__.py
3. Runs bench migrate
4. Click "Verify Files"
5. All files verified ✓
```

## Tips for Best Results

### Prompting Tips

1. **Be Specific**: "Add a Data field called 'email' with email validation" is better than "add email field"

2. **Use Frappe Terminology**: Use terms like "Link field", "Select field", "Currency field" that Frappe understands

3. **Request Complete Definitions**: Ask for "complete JSON definition" to get the full DocType structure

4. **Iterate Gradually**: Make changes one at a time rather than requesting many changes at once

### Working with Claude

1. **Main Chat for Architecture**: Use main app chat for high-level design discussions

2. **DocType Chat for Details**: Use DocType-specific chats for field-level modifications

3. **Review Before Applying**: Always review the JSON definitions before clicking Apply Changes

4. **Test After Each Change**: Test your DocTypes after applying changes to catch issues early

### File Management

1. **Backup First**: Always backup your app before applying major changes

2. **Version Control**: Use git to track changes to your app

3. **Verify Always**: Always run verification after applying changes

## Troubleshooting Common Issues

### Issue: "Claude API Key not configured"
**Solution**: Go to Claude API Settings and add your API key

### Issue: "Apps path not configured"
**Solution**: Set the Apps Path in Claude API Settings to your frappe-bench/apps directory

### Issue: "Files not created"
**Solution**: 
- Check directory permissions
- Verify Apps Path is correct
- Check File Change Log for error details

### Issue: "bench migrate failed"
**Solution**:
- Check if bench is in your PATH
- Verify you're in the correct environment
- Try running manually: `bench --site sitename migrate`

### Issue: "DocType not appearing in UI"
**Solution**:
- Clear cache: `bench --site sitename clear-cache`
- Restart: `bench restart`
- Check the JSON file is valid

## Advanced Usage

### Custom Python Code

After Claude creates the basic DocType structure, you can add custom Python code:

1. Open the .py file in your editor
2. Add methods to the DocType class
3. Save and reload

Example:
```python
class Customer(Document):
    def validate(self):
        if self.email:
            self.email = self.email.lower()
    
    def before_save(self):
        if not self.customer_code:
            self.customer_code = self.generate_customer_code()
    
    def generate_customer_code(self):
        # Custom logic
        return f"CUST-{self.name[-5:]}"
```

### Adding Client Scripts

Create client scripts in the Frappe UI:
1. Go to Client Script List
2. Create new Client Script
3. Select your DocType
4. Add JavaScript code

### Adding Server Scripts

Create server scripts in the Frappe UI:
1. Go to Server Script List
2. Create new Server Script
3. Select DocType and event
4. Add Python code

## Next Steps

After mastering the basics:

1. Explore creating more complex DocTypes with multiple field types
2. Learn about Frappe relationships (Link, Table, Child Table)
3. Create web views and portals
4. Add custom workflows
5. Create reports and dashboards

## Getting Help

1. Check conversation history in your session
2. Review File Change Log for operation details
3. Read Frappe documentation: https://frappeframework.com/docs
4. Ask Claude for explanations and guidance

---

Happy building with Leet Devops! 🚀
