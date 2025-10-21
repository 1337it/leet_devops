# Leet DevOps - Installation & Setup Guide

## Prerequisites

Before installing Leet DevOps, ensure you have:

1. **Frappe Framework** installed (v14 or later)
   - If not installed, follow: https://frappeframework.com/docs/user/en/installation
   
2. **Python 3.8+** 
   ```bash
   python3 --version
   ```

3. **Anthropic API Key**
   - Sign up at: https://console.anthropic.com/
   - Create an API key from the dashboard

## Installation Steps

### Step 1: Download the App

Navigate to your Frappe bench directory and get the app:

```bash
cd frappe-bench
bench get-app https://github.com/your-username/leet_devops.git
```

Or if you have the app locally:

```bash
cd frappe-bench
bench get-app /path/to/leet_devops
```

### Step 2: Install on Site

Install the app on your site:

```bash
bench --site your-site.local install-app leet_devops
```

Replace `your-site.local` with your actual site name.

### Step 3: Install Dependencies

Install required Python packages:

```bash
bench pip install anthropic
```

### Step 4: Restart Services

Restart bench to load the new app:

```bash
bench restart
```

If using production setup:

```bash
sudo service supervisor restart
sudo service nginx reload
```

### Step 5: Run Migrations

Ensure all database changes are applied:

```bash
bench --site your-site.local migrate
```

### Step 6: Clear Cache

Clear cache to load new assets:

```bash
bench --site your-site.local clear-cache
bench build
```

## Configuration

### Configure DevOps Settings

1. Login to your Frappe site
2. Go to **Settings** > **DevOps Settings**
3. Fill in the following:

#### API Configuration
- **Claude API Key**: Paste your Anthropic API key
- **Max Tokens**: Set to 4096 (or higher based on your needs)
- **Model**: Select `claude-sonnet-4-20250514` (recommended)
- **Temperature**: Set to 1.0 (adjust for creativity: 0=focused, 2=creative)

#### Default App
- **Target App Name**: Enter the name of your Frappe app (e.g., "my_custom_app")
- **App Path**: Full path to your app (e.g., "/home/frappe/frappe-bench/apps/my_custom_app")

4. Click **Save**

## Verification

### Test the Installation

1. **Check App Installation**
   ```bash
   bench --site your-site.local list-apps
   ```
   You should see `leet_devops` in the list.

2. **Access Chat Interface**
   - Navigate to: `http://your-site.local/app/chat-interface`
   - You should see the Chat Interface page

3. **Create Test Session**
   - Click "New Session"
   - Enter title: "Test Session"
   - Enter target app: Your app name
   - Click "Create"

4. **Send Test Message**
   - Type: "Hello, can you help me create a DocType?"
   - Press Ctrl+Enter or click Send
   - You should see a streaming response from Claude

## Troubleshooting

### Issue: App Not Showing in List

**Solution:**
```bash
bench get-app leet_devops
bench --site your-site.local install-app leet_devops
```

### Issue: Import Errors

**Solution:**
```bash
bench pip install anthropic --upgrade
bench restart
```

### Issue: Chat Interface Not Loading

**Solution:**
```bash
bench clear-cache
bench build --app leet_devops
bench restart
```

### Issue: API Key Not Working

**Verify:**
1. API key is correct (no extra spaces)
2. API key has sufficient credits
3. Check Anthropic console for API status

### Issue: Streaming Not Working

**Check:**
1. Redis is running:
   ```bash
   redis-cli ping
   ```
2. SocketIO is enabled in site_config.json:
   ```json
   {
     "socketio_port": 9000
   }
   ```
3. Restart bench:
   ```bash
   bench restart
   ```

### Issue: Permission Denied

**Solution:**
Add System Manager role to your user:
```bash
bench --site your-site.local add-system-manager username
```

## Development Mode Setup

If you want to develop or customize the app:

1. **Enable Developer Mode**
   ```bash
   bench --site your-site.local set-config developer_mode 1
   ```

2. **Watch for Changes**
   ```bash
   bench watch
   ```

3. **View Logs**
   ```bash
   bench --site your-site.local console
   # Or
   tail -f sites/your-site.local/logs/web.error.log
   ```

## Updating the App

To update Leet DevOps to the latest version:

```bash
cd frappe-bench/apps/leet_devops
git pull origin main

cd ../..
bench --site your-site.local migrate
bench clear-cache
bench build --app leet_devops
bench restart
```

## Uninstallation

If you need to uninstall the app:

```bash
bench --site your-site.local uninstall-app leet_devops
bench remove-app leet_devops
```

**Warning:** This will delete all sessions, messages, and settings.

## Production Setup

### Nginx Configuration

If running in production, ensure your nginx configuration includes WebSocket support for streaming:

```nginx
location /socket.io {
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header X-Frappe-Site-Name your-site.local;
    proxy_pass http://127.0.0.1:9000/socket.io;
}
```

### Supervisor Configuration

Ensure SocketIO process is running:

```bash
sudo supervisorctl status frappe-bench-frappe-socketio
```

If not running:

```bash
sudo supervisorctl start frappe-bench-frappe-socketio
```

## Security Best Practices

1. **Protect API Key**: Never commit API keys to version control
2. **Use HTTPS**: Always use HTTPS in production
3. **Limit Access**: Only grant access to trusted users
4. **Monitor Usage**: Regularly check Anthropic API usage
5. **Backup Data**: Regular backups of your site

## Next Steps

After successful installation:

1. Read the [User Guide](USER_GUIDE.md)
2. Explore example sessions
3. Configure your target app
4. Start generating code!

## Support

For issues or questions:
- GitHub Issues: [Your repo issues page]
- Email: info@leetdevops.com
- Documentation: [Your docs link]

## Version Check

To check your installed version:

```bash
bench version
# Or
cd frappe-bench/apps/leet_devops
cat leet_devops/__init__.py
```

Current Version: 0.0.1
