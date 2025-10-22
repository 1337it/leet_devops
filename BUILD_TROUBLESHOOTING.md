# Leet Devops - Build Troubleshooting Guide

## Common Build Errors and Solutions

### Error: "paths[0]" argument must be of type string. Received undefined

**Symptom:**
```
TypeError [ERR_INVALID_ARG_TYPE]: The "paths[0]" argument must be of type string. Received undefined
```

**Cause:**
This error occurs when Frappe's esbuild process cannot find the expected directory structure or files.

**Solution:**
The app now includes all required directories and files:
- ✅ `public/js/` directory
- ✅ `public/css/` directory
- ✅ `public/build.json` file
- ✅ `public/images/` directory
- ✅ `templates/includes/` directory
- ✅ All necessary `__init__.py` files

**If you still encounter this error:**

1. Verify directory structure:
```bash
cd /path/to/frappe-bench/apps/leet_devops
ls -la leet_devops/public/
```

You should see:
- build.json
- css/
- images/
- js/

2. Ensure all __init__.py files exist:
```bash
find leet_devops -name "__init__.py" -type f
```

3. Clear build cache:
```bash
cd /path/to/frappe-bench
bench clear-cache
bench clear-website-cache
```

4. Try building again:
```bash
bench build --app leet_devops
```

### Error: Module not found or Import errors

**Solution:**
Ensure the app is properly installed:

```bash
bench --site your-site-name install-app leet_devops
```

### Error: DocTypes not visible after installation

**Solution:**
1. Clear cache:
```bash
bench --site your-site-name clear-cache
```

2. Migrate database:
```bash
bench --site your-site-name migrate
```

3. Restart:
```bash
bench restart
```

### Error: Web page not loading (/app_chat)

**Symptom:**
404 error when accessing `/app_chat?session=xxx`

**Solution:**
1. Check that `www/app_chat/index.html` and `www/app_chat/index.py` exist

2. Clear website cache:
```bash
bench --site your-site-name clear-website-cache
```

3. Rebuild:
```bash
bench build --app leet_devops
```

### Error: JavaScript not loading in chat interface

**Symptom:**
Chat interface loads but buttons don't work

**Solution:**
1. Check browser console for errors (F12)

2. Verify JS file exists:
```bash
ls -la leet_devops/public/js/app_chat.js
```

3. Clear cache and rebuild:
```bash
bench clear-cache
bench build --app leet_devops
bench restart
```

## Installation Checklist

After extracting and copying the app, verify:

- [ ] App is in the correct directory: `/path/to/frappe-bench/apps/leet_devops`
- [ ] All files are extracted (not just the folder)
- [ ] Permissions are correct (readable by frappe user)
- [ ] App is installed on site: `bench --site sitename list-apps` shows leet_devops
- [ ] Database is migrated: No pending migrations
- [ ] Cache is clear
- [ ] Build completed successfully

## Build Process Steps

The correct installation and build sequence:

```bash
# 1. Copy app to apps directory
cp -r leet_devops /path/to/frappe-bench/apps/

# 2. Change to bench directory
cd /path/to/frappe-bench

# 3. Install app (this also runs build)
bench --site your-site-name install-app leet_devops

# 4. If build fails, try manual build
bench build --app leet_devops

# 5. Clear cache
bench --site your-site-name clear-cache

# 6. Restart
bench restart

# 7. Verify installation
bench --site your-site-name list-apps
```

## Verifying Successful Installation

After installation, you should be able to:

1. **Access Settings:**
   - Search for "Claude API Settings" in Awesome Bar (Ctrl+K)
   - Should open without errors

2. **Create Session:**
   - Go to "App Development Session" list
   - Click "New"
   - Should be able to create a new session

3. **Access Chat:**
   - Open a session
   - Click on session name
   - Should redirect to `/app_chat?session=XXX`
   - Chat interface should load

4. **Check Logs:**
```bash
# Check for any errors
tail -f /path/to/frappe-bench/logs/web.error.log
tail -f /path/to/frappe-bench/logs/worker.error.log
```

## Development Mode

If you're developing or modifying the app:

```bash
# Watch for changes and rebuild automatically
bench watch

# Or manually rebuild after each change
bench build --app leet_devops
```

## Production Mode

For production deployment:

```bash
# Build with production optimizations
bench build --production

# If using supervisor
sudo supervisorctl restart all
```

## Still Having Issues?

1. **Check Frappe Version:**
   ```bash
   bench version
   ```
   Ensure you're on Frappe v13 or later.

2. **Check Node Version:**
   ```bash
   node --version
   ```
   Should be v14 or later.

3. **Check Permissions:**
   ```bash
   ls -la apps/leet_devops/
   ```
   All files should be readable.

4. **Reinstall:**
   ```bash
   bench --site your-site-name uninstall-app leet_devops
   bench --site your-site-name install-app leet_devops
   ```

5. **Check File Change Log:**
   - Go to "File Change Log" list
   - Look for any error messages

6. **Enable Developer Mode:**
   In site_config.json, add:
   ```json
   {
     "developer_mode": 1
   }
   ```
   Then restart bench.

## Getting Help

If you continue to experience issues:

1. Check the error logs in `/path/to/frappe-bench/logs/`
2. Review the installation steps in INSTALL.md
3. Verify all prerequisites are met
4. Check Frappe documentation for your version

---

Most build issues are resolved by ensuring:
- Correct directory structure
- All required files present
- Proper installation sequence
- Cache cleared after installation
