# Leet Devops - User Guide

## How to Effectively Use Claude for App Generation

This guide will help you get the most out of Leet Devops by teaching you how to communicate effectively with Claude AI.

## Understanding the System

### Session Structure

**Main Session**
- Your primary conversation with Claude about the overall app
- Used for high-level design decisions
- Creates the initial app structure
- Generates DocType specifications

**DocType Sessions (Child Sessions)**
- Dedicated conversations for specific DocTypes
- Fine-tune individual DocType details
- Modify fields, add validations, adjust permissions
- Each DocType has its own context and conversation history

### Workflow

1. **Start Main Session** → Describe your app requirements
2. **Claude Generates Plan** → Review DocType suggestions
3. **DocType Sessions Created** → Each DocType gets a child session
4. **Refine DocTypes** → Click on DocTypes to chat about specific ones
5. **Review Changes** → Check pending file operations
6. **Apply Changes** → Create files and run migrations
7. **Verify** → Confirm all files were created successfully

## Communication Best Practices

### 1. Start with a Clear Vision

❌ **Bad:**
```
Make me an app
```

✅ **Good:**
```
I need a Restaurant Management app with the following features:
- Menu management (dishes, categories, prices)
- Order tracking (table numbers, order items, status)
- Customer reservations
- Inventory management for ingredients
```

### 2. Be Specific About DocTypes

❌ **Bad:**
```
Add some fields to Customer
```

✅ **Good:**
```
For the Customer DocType, add:
- Customer Type (Select: Regular, VIP, Corporate)
- Credit Limit (Currency)
- Payment Terms (Select: Cash, 30 Days, 60 Days)
- Loyalty Points (Int, default 0, read-only)
Make Credit Limit required only if Customer Type is Corporate.
```

### 3. Specify Field Properties

❌ **Bad:**
```
Add email and phone
```

✅ **Good:**
```
Add these fields:
- Email Address (Data, required, unique, with email validation)
- Phone Number (Data, optional, format: +XX-XXX-XXX-XXXX)
- Alternative Phone (Data, optional)
```

### 4. Request Relationships Clearly

❌ **Bad:**
```
Connect orders to customers
```

✅ **Good:**
```
Create a Link field in the Order DocType:
- Field name: customer
- Links to: Customer
- Required: Yes
- Fetch customer's email and phone for quick reference
```

### 5. Ask for Child Tables

❌ **Bad:**
```
Orders should have items
```

✅ **Good:**
```
Create an Order Items child table with:
- Item Name (Link to Item)
- Quantity (Int, default 1)
- Rate (Currency, fetch from Item)
- Amount (Currency, read-only, calculated as Quantity * Rate)
- Notes (Text, optional)
```

## Example Conversations

### Example 1: Creating a Simple App

**You:**
```
Create a Library Management app with:
1. Book DocType: title, author, ISBN, status (Available/Borrowed)
2. Member DocType: name, email, phone, membership date
3. Borrowing DocType: member, book, borrow date, return date
```

**Claude Response:**
```
I'll create a Library Management app with three DocTypes:

1. Book DocType...
[Detailed specifications]

2. Member DocType...
[Detailed specifications]

3. Borrowing DocType...
[Detailed specifications]

I'll now create the DocType sessions for each of these.
```

**What Happens:**
- Three DocType sessions are created
- You can click on each to refine them
- Files are prepared for creation

### Example 2: Refining a DocType

**In Book DocType Session:**

**You:**
```
Add these features to Book:
- Publication Year (Int)
- Category (Select: Fiction, Non-Fiction, Reference, Children)
- Shelf Location (Data)
- Cover Image (Attach Image)
- Make ISBN unique and required
```

**Claude Response:**
```
I'll update the Book DocType with these fields...
[Shows updated JSON]
```

### Example 3: Adding Validations

**You:**
```
In the Borrowing DocType:
- Validate that return date is after borrow date
- Automatically set status to 'Borrowed' when saved
- Check if book is available before allowing borrowing
```

**Claude Response:**
```
I'll add these validations to the Borrowing DocType...
[Provides Python code for validation]
```

## Advanced Features

### 1. Custom Scripts

**Request:**
```
Add client-side script to Order:
- When item is selected, automatically fetch its price
- Calculate total amount as sum of all items
- Show warning if total exceeds customer's credit limit
```

### 2. Server Scripts

**Request:**
```
Add server-side logic to Invoice:
- Before saving, validate tax calculations
- After saving, update customer's outstanding balance
- On cancel, reverse all ledger entries
```

### 3. Permissions

**Request:**
```
Set permissions for Order DocType:
- Sales User: Can create and read own orders
- Sales Manager: Can read, write, delete all orders
- Accounts User: Can only read submitted orders
- Customer: Can read only their own orders (portal access)
```

### 4. Reports and Dashboards

**Request:**
```
Create a Sales Dashboard with:
- Total revenue this month (card)
- Top 5 customers by revenue (chart)
- Pending orders count (indicator)
- Recent order list
```

## Tips for Success

### 1. Iterate Gradually

Start with basic structure, then add complexity:
```
Session 1: Create basic DocTypes
Session 2: Add validations
Session 3: Add custom scripts
Session 4: Configure permissions
Session 5: Create reports
```

### 2. Use DocType Sessions

When you need to modify a specific DocType:
1. Click on it in the right sidebar
2. Chat specifically about that DocType
3. All context is preserved for that DocType

### 3. Review Before Applying

Always check:
- File paths are correct
- No duplicate operations
- Related DocType mentioned correctly
- Field names follow conventions (snake_case)

### 4. Verify After Applying

Use the Verify button to:
- Confirm all files were created
- Check for missing files
- Ensure proper structure

### 5. Handle Errors Gracefully

If something fails:
1. Read the error message carefully
2. Go back to the relevant DocType session
3. Ask Claude to fix the issue
4. Apply changes again

## Common Patterns

### Creating Master DocTypes

```
Create a [Name] DocType as a master with:
- Name field (required, unique)
- Description (Text)
- Is Active (Check, default true)
- Standard naming (autoname: field:name)
```

### Creating Transaction DocTypes

```
Create a [Name] DocType as a transaction with:
- Naming series (format: PREFIX-.YYYY.-.#####)
- Date field (default: today)
- Status (Select: Draft, Submitted, Cancelled)
- Enable workflow
- Track changes
```

### Creating Child Tables

```
Create a child table [Name] with:
- Parent DocType: [ParentName]
- Fields: [list fields]
- No permissions (inherited from parent)
- No naming
```

## Troubleshooting

### Issue: DocType Not Created

**Solution:**
- Check if files were created (Verify button)
- Look for error messages in the console
- Ensure app path is correct in settings
- Try running `bench migrate` manually

### Issue: Fields Not Showing

**Solution:**
- Clear cache (`bench clear-cache`)
- Reload the form
- Check field properties (hidden, read_only)
- Verify field names are unique

### Issue: Validation Not Working

**Solution:**
- Check Python syntax in the validation code
- Ensure validation is in the correct method
- Look at error logs (`bench console`)
- Test validation conditions

## Best Practices Summary

1. ✅ Be specific and detailed
2. ✅ Use proper field types
3. ✅ Specify validations clearly
4. ✅ Request complete features
5. ✅ Review before applying
6. ✅ Verify after applying
7. ✅ Use DocType sessions for refinement
8. ✅ Iterate gradually
9. ✅ Keep conversations organized
10. ✅ Test thoroughly after creation

## Getting Help

If you encounter issues:

1. **Check the logs**: Look at Frappe error logs
2. **Review Claude's response**: Make sure you understood correctly
3. **Ask for clarification**: Go back and ask Claude to explain
4. **Start a new session**: If things get messy
5. **Manual fixes**: You can always edit files manually

## Remember

- Claude is a helpful assistant, but review all code
- Test in development environment first
- Keep backups of your app
- Document your customizations
- Follow Frappe best practices

---

Happy app building! 🚀
