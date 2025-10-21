#!/bin/bash

# Leet DevOps Installation Script
# This script helps install and configure Leet DevOps

set -e

echo "================================================"
echo "Leet DevOps Installation Script"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if running from frappe-bench directory
if [ ! -d "apps" ] || [ ! -d "sites" ]; then
    print_error "Please run this script from your frappe-bench directory"
    exit 1
fi

print_success "Running from frappe-bench directory"

# Check if app already exists
if [ -d "apps/leet_devops" ]; then
    print_info "Leet DevOps app already exists"
    read -p "Do you want to reinstall? (y/n): " reinstall
    if [ "$reinstall" != "y" ]; then
        echo "Installation cancelled"
        exit 0
    fi
    print_info "Removing existing app..."
    rm -rf apps/leet_devops
fi

# Get site name
echo ""
read -p "Enter your site name (e.g., site1.local): " SITE_NAME

if [ -z "$SITE_NAME" ]; then
    print_error "Site name is required"
    exit 1
fi

# Check if site exists
if [ ! -d "sites/$SITE_NAME" ]; then
    print_error "Site $SITE_NAME does not exist"
    exit 1
fi

print_success "Site $SITE_NAME found"

# Install the app
echo ""
print_info "Installing Leet DevOps..."

# Get the app
if [ -d "../leet_devops" ]; then
    print_info "Getting app from parent directory..."
    bench get-app ../leet_devops
elif [ ! -z "$1" ]; then
    print_info "Getting app from: $1"
    bench get-app "$1"
else
    print_info "Getting app from current directory..."
    bench get-app $(pwd)
fi

print_success "App downloaded"

# Install dependencies
echo ""
print_info "Installing Python dependencies..."
bench pip install anthropic
print_success "Dependencies installed"

# Install app on site
echo ""
print_info "Installing app on site $SITE_NAME..."
bench --site $SITE_NAME install-app leet_devops
print_success "App installed on site"

# Migrate
echo ""
print_info "Running migrations..."
bench --site $SITE_NAME migrate
print_success "Migrations completed"

# Clear cache and build
echo ""
print_info "Clearing cache and building assets..."
bench --site $SITE_NAME clear-cache
bench build --app leet_devops
print_success "Cache cleared and assets built"

# Restart bench
echo ""
print_info "Restarting bench..."
bench restart
print_success "Bench restarted"

# Configuration
echo ""
echo "================================================"
echo "Installation Complete!"
echo "================================================"
echo ""
print_success "Leet DevOps has been successfully installed"
echo ""
echo "Next Steps:"
echo "1. Login to your site: http://$SITE_NAME"
echo "2. Go to Settings > DevOps Settings"
echo "3. Configure your Claude API key"
echo "4. Navigate to Chat Interface to start"
echo ""
echo "Documentation:"
echo "- Installation Guide: apps/leet_devops/INSTALLATION_GUIDE.md"
echo "- User Guide: apps/leet_devops/USER_GUIDE.md"
echo ""
print_info "For support, visit: https://github.com/your-repo/leet_devops"
echo ""
