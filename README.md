# Leet DevOps

An AI-powered development assistant for Frappe Framework that integrates Claude AI directly into your Frappe dashboard.

## Features

- 🤖 **AI Assistant**: Chat with Claude AI to get development help
- 💻 **Code Generation**: Generate DocTypes, API endpoints, and custom scripts
- 🔄 **Change Preview**: See changes before applying them
- ✅ **Apply/Revert**: Safely apply or revert code changes
- 📝 **Session Management**: Organize your development conversations
- 🎯 **Context-Aware**: Claude understands your Frappe setup

## Installation

1. Get the app:
```bash
cd ~/frappe-bench
bench get-app https://github.com/yourusername/leet_devops
```

2. Install on your site:
```bash
bench --site your-site-name install-app leet_devops
```

3. Configure Claude API key:
Add to your `site_config.json`:
```json
{
  "claude_api_key": "sk-ant-..."
}
```

4. Restart bench:
```bash
bench restart
```

## Usage

1. Navigate to **Leet DevOps** module in your Frappe desk
2. Create a new Dev Chat Session
3. Start chatting with the AI assistant
4. When code changes are suggested, review and apply them
5. Test the changes in your environment
6. Confirm to move the code to your custom app

## Example Prompts

- "Create a new DocType called 'Project Task' with fields for title, description, and status"
- "Add a custom API endpoint to get all active customers"
- "Create a client script to validate email format on Contact form"
- "Help me create a report for monthly sales analysis"

## Development

To contribute or modify:

```bash
cd ~/frappe-bench/apps/leet_devops
# Make your changes
bench build
bench restart
```

## Security Notes

- Keep your Claude API key secure
- Review all AI-generated code before applying
- Test changes in development environment first
- Always backup before applying changes to production

## License

MIT
```

### license.txt
```
MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Next Steps

1. **Create the GitHub Repository**:
   ```bash
   cd ~/frappe-bench/apps
   mkdir leet_devops
   cd leet_devops
   git init
   # Copy all files from the structure above
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/leet_devops.git
   git push -u origin main
   ```

2. **Install the App**:
   Follow the installation instructions in the README

3. **Configure Claude API**:
   Add your API key to site_config.json

4. **Start Using**:
   Navigate to Leet DevOps module and start chatting!
