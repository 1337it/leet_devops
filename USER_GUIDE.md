# Leet DevOps - User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Creating Sessions](#creating-sessions)
3. [Chat Interface](#chat-interface)
4. [Working with Child Sessions](#working-with-child-sessions)
5. [Generating Code](#generating-code)
6. [Best Practices](#best-practices)
7. [Examples](#examples)

## Getting Started

### First Login

1. Navigate to your Frappe site
2. Go to **Chat Interface** page from the desk
   - Or visit: `http://your-site.local/app/chat-interface`

### Understanding the Interface

The Chat Interface has three main areas:

1. **Header**: Shows session title and actions
2. **Messages Area**: Displays conversation history
3. **Input Area**: Where you type messages

## Creating Sessions

### Main Session

Main sessions are for overall project planning and coordination.

**To Create:**
1. Click **"New Session"** button
2. Fill in:
   - **Title**: "Customer Portal Development"
   - **Target App**: "my_custom_app"
   - **Session Type**: "Main"
3. Click **"Create"**

### Child Sessions

Child sessions are automatically created by Claude when specific artifacts are discussed. Types:

- **DocType**: For creating document types
- **Function**: For API endpoints and utilities
- **Report**: For custom reports
- **Page**: For custom pages

**Automatic Creation:**
Claude analyzes your conversation and creates child sessions when you mention:
- "create a doctype"
- "build a function"
- "make a report"
- "design a page"

## Chat Interface

### Sending Messages

**Method 1: Click Send**
1. Type your message
2. Click the **Send** button

**Method 2: Keyboard Shortcut**
1. Type your message
2. Press **Ctrl+Enter**

### Message Types

- **User Messages**: Appear on the right (blue)
- **Assistant Messages**: Appear on the left (white)
- **Streaming Messages**: Show with a blue border while Claude is typing

### Streaming Responses

Claude's responses stream in real-time:
1. You see a typing indicator (●●●)
2. Text appears character by character
3. Response completes and formatting applies

## Working with Child Sessions

### Viewing Child Sessions

1. Click **"Child Sessions"** button in header
2. See all child sessions with:
   - Title
   - Type badge (DocType, Function, etc.)
   - Last modified time
   - Status

### Opening Child Sessions

1. In the Child Sessions dialog
2. Click **"Open"** on any session
3. Opens the session in a new view

### Context Inheritance

Child sessions automatically inherit:
- Parent session context
- Target app information
- Previous conversation history (relevant parts)

## Generating Code

### DocType Generation

**Example Request:**
```
Create a Customer Feedback DocType with these fields:
- Customer (Link to Customer)
- Rating (Select: 1-5 stars)
- Feedback Text (Text Editor)
- Category (Select: Product, Service, Support)
- Status (Select: New, Reviewed, Closed)
```

**Claude Will Provide:**
1. Complete JSON definition
2. Python controller with validation
3. JavaScript for client-side logic
4. Installation instructions
5. Best practices

### API Function Generation

**Example Request:**
```
Create an API function to calculate delivery charges based on:
- Weight (in kg)
- Distance (in km)
- Express delivery flag

Base rate: $5
Per kg: $2
Per km: $0.5
Express: 50% surcharge
```

**Claude Will Provide:**
1. Python function with @frappe.whitelist()
2. Input validation
3. Error handling
4. Documentation
5. Usage examples

### Report Generation

**Example Request:**
```
Create a Sales Summary Report showing:
- Date range filter
- Total sales by customer
- Payment status breakdown
- Export to Excel option
```

**Claude Will Provide:**
1. Report JSON definition
2. Python query logic
3. JavaScript for filters
4. Formatting options

## Best Practices

### 1. Be Specific

❌ **Poor**: "Make a customer thing"
✅ **Good**: "Create a Customer Feedback DocType with rating and comments fields"

### 2. Provide Context

Include information about:
- Business requirements
- Field types needed
- Validation rules
- Relationships to other DocTypes

### 3. Use Multiple Messages

Instead of one huge message, break it down:

**Message 1:**
```
I need a Task Management system
```

**Message 2:**
```
Each task should have:
- Title
- Description
- Priority (High, Medium, Low)
- Assigned to (User)
- Due date
```

**Message 3:**
```
Add a status workflow: New → In Progress → Completed
```

### 4. Review Generated Code

Always:
- Read through generated code
- Test in development environment
- Modify as needed for your use case
- Add additional validation if required

### 5. Leverage Child Sessions

- Use child sessions for focused work
- Keep related code in the same child session
- Switch between sessions as needed

### 6. Save Important Code

Copy generated code to your app immediately:
1. Create the files in your app directory
2. Run bench migrate
3. Test thoroughly

## Examples

### Example 1: E-commerce Product Catalog

**Session Setup:**
- Title: "E-commerce Product Management"
- Target App: "ecommerce_app"

**Conversation:**

**User:**
```
I need to build a product catalog system. Let's start with the Product DocType.
```

**Claude:**
```
I'll help you create a comprehensive Product DocType. Let me design this with 
e-commerce best practices in mind.

[Provides complete Product DocType JSON and code]
```

**User:**
```
Now I need a Product Category DocType with hierarchical categories.
```

**Claude:**
```
I'll create a Product Category DocType with tree structure support...
[Creates child session automatically]
[Provides Category DocType with tree view]
```

### Example 2: Inventory Management

**Session Setup:**
- Title: "Warehouse Management System"
- Target App: "warehouse_app"

**Conversation:**

**User:**
```
Create a Stock Entry DocType for tracking inventory movements.
```

**Claude:**
```
I'll create a Stock Entry DocType with the following structure:
[Provides detailed Stock Entry DocType]
```

**User:**
```
Add a function to check available stock for an item in a specific warehouse.
```

**Claude:**
```
[Creates child session for Function]
I'll create a utility function for stock availability...
[Provides complete function with error handling]
```

### Example 3: HR Management

**Session Setup:**
- Title: "HR Management Portal"
- Target App: "hr_app"

**Conversation Flow:**
1. Create Employee DocType
2. Create Leave Application DocType
3. Create approval workflow function
4. Create leave balance report
5. Create employee dashboard page

Each item automatically gets its own child session for focused development.

## Tips and Tricks

### Keyboard Shortcuts

- **Ctrl+Enter**: Send message
- **Esc**: Clear input (custom implementation)

### Markdown Support

Claude's responses support basic markdown:
- `code` for inline code
- ``` blocks for code blocks
- **bold** text
- Links and more

### Copy Code Easily

- Hover over code blocks
- Look for copy button (if implemented)
- Or select and copy manually

### Session Organization

**Naming Convention:**
- Main: "[Project Name] - Main"
- Child: "[Artifact Name] - [Type]"

Example:
- "CRM System - Main"
- "Lead DocType - DocType"
- "Lead Assignment - Function"

### Context Management

Add context at the start:
```
Context: I'm building a multi-tenant SaaS application with role-based access.
Target users: B2B customers with team features.
```

Claude will remember this throughout the session.

## Common Use Cases

### 1. Creating Standard Forms
- Customer forms
- Product catalogs
- Invoice templates
- User profiles

### 2. Building APIs
- REST endpoints
- Data validation
- Third-party integrations
- Webhook handlers

### 3. Report Generation
- Sales reports
- Analytics dashboards
- KPI trackers
- Export functionality

### 4. Workflow Automation
- Approval workflows
- Email notifications
- Status transitions
- Automated tasks

### 5. Custom Pages
- Dashboards
- Admin panels
- User portals
- Analytics views

## Troubleshooting

### Message Not Sending

**Check:**
- API key configured
- Internet connection
- Token limits not exceeded

### No Response from Claude

**Try:**
- Refresh page
- Check API credits
- Verify API key validity

### Code Not Working

**Steps:**
1. Copy exact code from Claude
2. Check file paths
3. Run migrate
4. Restart bench
5. Clear cache

### Session Lost

**Recovery:**
- Check Recent Sessions on home page
- Use session search
- Child sessions remain linked

## Advanced Features

### Custom Prompts

You can guide Claude with specific instructions:

```
Generate a DocType following these rules:
- Use snake_case for field names
- Add docstrings to all methods
- Include comprehensive error handling
- Add unit test structure
```

### Batch Operations

Generate multiple related items:

```
Create these DocTypes:
1. Customer
2. Order
3. Order Item
4. Payment

Link them appropriately with proper relationships.
```

### Code Review

Ask Claude to review existing code:

```
Review this code and suggest improvements:
[paste your code]
```

## Next Steps

- Explore the [API Documentation](API_DOCS.md)
- Read [Contributing Guidelines](CONTRIBUTING.md)
- Check out [Example Projects](EXAMPLES.md)

## Getting Help

- Check the FAQ section
- Search existing sessions
- Contact support
- Join community forum

Remember: Claude is your AI pair programmer. The more context you provide, the better code you'll get!
