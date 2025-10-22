# Automatic Code Application Guide

## Overview

Leet DevOps now features **automatic code application** - no more manual copy-pasting! With a single button click, Claude's generated code is automatically:

1. ✅ Parsed and extracted
2. ✅ Organized into proper file structure
3. ✅ Written to your app directory
4. ✅ Migrated to the database
5. ✅ Ready to use immediately

## How It Works

### Step 1: Generate Code with Claude

Chat with Claude as usual:

```
You: Create a Task DocType with title, description, and status fields

Claude: I'll create a complete Task DocType for you...
[Provides JSON, Python, and JavaScript code]
```

### Step 2: Apply Changes

After Claude responds, you'll see two buttons:

- **🔵 Preview** - See what will be applied before committing
- **🟢 Apply Changes** - Automatically apply all changes

### Step 3: Preview (Optional)

Click **Preview** to see:
- What files will be created
- Where they'll be placed
- What type of artifact each is

Example preview:
```
✓ DocType: Task
  Description: Will create json file for DocType: Task
  Path: my_app/my_module/doctype/task/
  Action: Create

✓ DocType: Task (Python)
  Description: Will create python file for DocType: Task
  Path: my_app/my_module/doctype/task/task.py
  Action: Create
```

### Step 4: Apply

Click **Apply Changes** and watch as:
1. Code is automatically extracted
2. Files are created in proper locations
3. Directories are auto-created as needed
4. Migration runs in background
5. Results are shown

### Step 5: Done!

Refresh your browser and your new DocType/Function is ready to use!

## What Gets Applied Automatically

### DocTypes

**Automatic Actions:**
- ✅ Create DocType JSON in correct module
- ✅ Create Python controller file
- ✅ Create JavaScript client-side file
- ✅ Create all necessary directories
- ✅ Add `__init__.py` files
- ✅ Run database migration

**File Structure Created:**
```
my_app/
└── my_app/
    └── my_module/
        └── doctype/
            └── task/
                ├── __init__.py
                ├── task.json
                ├── task.py
                └── task.js
```

### Functions/API Endpoints

**Automatic Actions:**
- ✅ Create function file in api/ directory
- ✅ Add @frappe.whitelist() decorator
- ✅ Include error handling
- ✅ Make immediately callable

**File Structure Created:**
```
my_app/
└── my_app/
    └── api/
        ├── __init__.py
        └── calculate_shipping.py
```

### Reports

**Automatic Actions:**
- ✅ Create report JSON definition
- ✅ Create Python query file
- ✅ Create JavaScript for filters
- ✅ Place in correct report directory

### Pages

**Automatic Actions:**
- ✅ Create page JSON
- ✅ Create page JavaScript
- ✅ Create page Python controller
- ✅ Register in app

## Code Format Requirements

For automatic application to work, Claude structures code like this:

### DocType JSON
```json
{
  "doctype": "DocType",
  "name": "Task",
  "fields": [...]
}
```

### Python Controller
```python
import frappe
from frappe.model.document import Document

class Task(Document):
    def validate(self):
        pass
```

### JavaScript
```javascript
frappe.ui.form.on('Task', {
    refresh: function(frm) {
        // Code here
    }
});
```

### API Function with Path
```python
# File: api/calculate_shipping.py
import frappe

@frappe.whitelist()
def calculate_shipping(weight, distance):
    """Calculate shipping cost"""
    return weight * 2 + distance * 0.5
```

## Advanced Features

### Automatic Module Detection

The system automatically:
- Detects existing modules in your app
- Uses the first available module
- Creates a default module if none exist
- Places artifacts in the right module

### Directory Management

Automatically creates:
- Module directories
- DocType subdirectories  
- API directories
- All necessary `__init__.py` files

### Migration Handling

After applying changes:
- Migration runs automatically in background
- You're notified when complete
- No manual `bench migrate` needed
- Cache is automatically cleared

### Error Handling

If something fails:
- Detailed error messages shown
- Partially applied changes logged
- Session artifacts tracking updated
- You can retry or fix manually

## Application Results

After applying, you'll see a detailed summary:

```
Success! Applied 3 artifact(s).

✓ doctype: Task
  Created json file for DocType: Task
  Path: /path/to/app/my_app/my_module/doctype/task/task.json

✓ doctype: Task
  Created python file for DocType: Task  
  Path: /path/to/app/my_app/my_module/doctype/task/task.py

✓ doctype: Task
  Created js file for DocType: Task
  Path: /path/to/app/my_app/my_module/doctype/task/task.js

Changes have been applied. Migration is running in the background.
You may need to refresh your browser to see the new DocTypes.
```

## Real-Time Updates

The system uses WebSocket for real-time updates:
- See migration progress
- Get notified when complete
- No page refresh needed during application
- Live status updates

## Troubleshooting

### "No artifacts found to apply"

**Cause:** Message doesn't contain code blocks
**Solution:** Ask Claude to provide complete code with proper formatting

### "App path not found"

**Cause:** App path not configured
**Solution:** 
1. Go to DevOps Settings
2. Set "App Path" to full path (e.g., `/home/frappe/frappe-bench/apps/my_app`)
3. Or ensure app is in `apps/` directory

### "Could not create file"

**Cause:** Permission issues
**Solution:**
```bash
# Fix permissions
cd frappe-bench/apps/my_app
chmod -R 755 .
chown -R frappe:frappe .
```

### "Migration failed"

**Cause:** Invalid DocType JSON
**Solution:**
1. Check error logs
2. Manually verify JSON syntax
3. Fix and retry

### Files created but not visible

**Cause:** Browser cache or migration not complete
**Solution:**
1. Wait for migration complete notification
2. Refresh browser (Ctrl+R)
3. Clear cache if needed: `bench clear-cache`

## Best Practices

### 1. Always Preview First

Before applying, click Preview to verify:
- Correct file paths
- Proper artifact detection
- No conflicts with existing files

### 2. One Artifact Type Per Message

For best results, generate one type at a time:

❌ **Avoid:**
```
Create Task DocType, Order DocType, and calculate_shipping function
```

✅ **Better:**
```
Message 1: Create Task DocType
[Apply]

Message 2: Create Order DocType
[Apply]

Message 3: Create calculate_shipping function
[Apply]
```

### 3. Verify in Development First

- Test in development environment
- Verify functionality
- Then apply in production

### 4. Keep Sessions Organized

- Use descriptive session names
- One feature per main session
- Let child sessions organize artifacts

### 5. Review Generated Code

Even with automatic application:
- Review code quality
- Check for security issues
- Ensure it meets requirements
- Customize as needed

## Manual Override

If automatic application doesn't work, you can always:

1. Copy code from message
2. Create files manually
3. Run `bench migrate`
4. Continue using Leet DevOps

## Configuration

### Required Settings

In **DevOps Settings**, configure:

1. **Target App Name**: e.g., "my_custom_app"
2. **App Path**: e.g., "/home/frappe/frappe-bench/apps/my_custom_app"

### Optional Settings

- **Max Tokens**: Higher for larger artifacts
- **Temperature**: Lower (0.7) for more consistent code

## Security Considerations

### Safe by Default

- All file paths validated
- Can only write within app directory
- No system files can be modified
- All actions logged

### Permissions

- Requires System Manager role
- Can be restricted further if needed
- All operations audited

### Code Review

- Always review generated code
- Check for security vulnerabilities
- Validate input handling
- Test thoroughly

## Performance

### Optimization Tips

1. **Smaller Artifacts**: Break into chunks for faster application
2. **Background Migration**: Doesn't block the UI
3. **Batch Operations**: Apply multiple artifacts at once
4. **Cache Clearing**: Automatic after application

### Expected Timings

- **Code Extraction**: < 1 second
- **File Creation**: < 2 seconds  
- **Migration**: 10-30 seconds (background)
- **Total**: ~30 seconds for typical DocType

## Examples

### Example 1: Complete DocType

**Input:**
```
Create a Customer Feedback DocType with:
- Customer (Link)
- Rating (1-5 stars)
- Comments (Text)
- Status (New/Reviewed)
```

**Output:**
- 3 files created automatically
- Migration runs
- Ready to use in ~30 seconds

### Example 2: API Function

**Input:**
```
Create an API to get customer feedback stats:
- Total feedback count
- Average rating
- Recent feedback
```

**Output:**
- 1 file created in api/
- Function immediately callable
- No migration needed

### Example 3: Multiple Related DocTypes

**Session:** E-commerce System

**Message 1:** Create Product DocType
[Apply] → Creates Product with 3 files

**Message 2:** Create Order DocType  
[Apply] → Creates Order with 3 files

**Message 3:** Create Order Item child table
[Apply] → Creates Order Item with files

All automatically linked and migrated!

## FAQ

**Q: Does this work for existing apps?**
A: Yes! Works with any Frappe app in your bench.

**Q: What if files already exist?**
A: Currently overwrites. Future version will have conflict resolution.

**Q: Can I undo changes?**
A: Use version control (git). Future version will have rollback.

**Q: Does it work with ERPNext?**
A: Yes, can create custom DocTypes in ERPNext or any Frappe app.

**Q: What about custom apps?**
A: Works perfectly! Just set the app name in settings.

**Q: Is it production-ready?**
A: Test thoroughly in development first. Review all generated code.

## Coming Soon

Future enhancements:
- 🔄 Rollback functionality
- ⚠️ Conflict detection and resolution
- 📝 Automatic git commits
- 🧪 Generated unit tests
- 📊 Application history tracking
- 🔍 Code quality checks

## Support

Need help?
- Check error logs in Frappe
- Review session artifacts
- Contact support
- Open GitHub issue

---

**With automatic code application, going from idea to working DocType takes seconds, not hours!**
