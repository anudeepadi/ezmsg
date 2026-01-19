#!/bin/bash

# =============================================================================
# Railway Deployment Script for EzMsg
# =============================================================================
# This script helps deploy EzMsg to Railway using the Railway CLI
#
# Prerequisites:
# 1. Install Railway CLI: npm i -g @railway/cli
# 2. Login: railway login
# 3. Create a new project on Railway dashboard first
# =============================================================================

set -e  # Exit on error

echo "🚂 EzMsg Railway Deployment"
echo "================================"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found!"
    echo "📦 Install it with: npm i -g @railway/cli"
    exit 1
fi

echo "✅ Railway CLI found"
echo ""

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged in to Railway"
    echo "🔐 Run: railway login"
    exit 1
fi

echo "✅ Logged in to Railway"
echo ""

# Link to project
echo "🔗 Linking to Railway project..."
echo "If this is your first time, select your project from the list."
echo ""

railway link

echo ""
echo "✅ Linked to project"
echo ""

# Prompt for service to deploy
echo "Which service would you like to deploy?"
echo "1) API (Backend)"
echo "2) Worker (Background Scheduler)"
echo "3) Web (Frontend)"
echo "4) All Services"
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo "🚀 Deploying API service..."
        cd api
        railway up
        cd ..
        ;;
    2)
        echo "🚀 Deploying Worker service..."
        cd worker
        railway up
        cd ..
        ;;
    3)
        echo "🚀 Deploying Web service..."
        cd web
        railway up
        cd ..
        ;;
    4)
        echo "🚀 Deploying all services..."
        echo ""
        echo "📦 Deploying API..."
        cd api && railway up && cd ..
        echo ""
        echo "📦 Deploying Worker..."
        cd worker && railway up && cd ..
        echo ""
        echo "📦 Deploying Web..."
        cd web && railway up && cd ..
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 View status: railway status"
echo "📝 View logs: railway logs"
echo "🌐 Open dashboard: railway open"
echo ""
echo "🎉 Done!"
