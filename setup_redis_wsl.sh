#!/bin/bash
# Redis Setup Script for WSL
# Run this in WSL: wsl bash setup_redis_wsl.sh

echo "🔧 Setting up Redis in WSL..."

# Update package list
sudo apt update

# Install Redis
echo "📦 Installing Redis..."
sudo apt install -y redis-server

# Configure Redis to start on boot
echo "⚙️  Configuring Redis..."
sudo systemctl enable redis-server

# Start Redis
echo "🚀 Starting Redis..."
sudo systemctl start redis-server

# Test Redis
echo "🧪 Testing Redis connection..."
redis-cli ping

if [ $? -eq 0 ]; then
    echo "✅ Redis is running!"
    echo ""
    echo "📊 Redis Status:"
    redis-cli info server | grep redis_version
    echo ""
    echo "✅ Setup complete! Redis is ready for Phase 2 caching."
else
    echo "❌ Redis setup failed. Please check the errors above."
fi


