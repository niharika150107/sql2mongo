#!/bin/bash

set -e  # stop on any error

echo "🚀 Starting full project setup..."

# -----------------------------
# 0. Install system dependencies
# -----------------------------
echo "📥 Installing system dependencies..."

sudo apt update
sudo apt install -y python3-venv postgresql postgresql-contrib

# -----------------------------
# 1. Python setup (clean)
# -----------------------------
echo "🐍 Setting up Python environment..."

# Remove old venv if exists
if [ -d "venv" ]; then
    echo "🧹 Removing existing virtual environment..."
    rm -rf venv
fi

# Create fresh venv
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# -----------------------------
# 2. PostgreSQL setup
# -----------------------------
echo "🐘 Setting up PostgreSQL..."

sudo service postgresql start

# Create DB (ignore error if exists)
sudo -u postgres psql -c "CREATE DATABASE transpiler_db;" 2>/dev/null || true

# Run schema + inserts
sudo -u postgres psql -d transpiler_db -f db/postgres_setup.sql

# -----------------------------
# 3. MongoDB setup using mongod
# -----------------------------
echo "🍃 Starting MongoDB..."

# Create data directory
mkdir -p ~/mongodb-data

# Kill existing mongod if running
pkill mongod 2>/dev/null || true

# Start mongod in background
mongod --dbpath ~/mongodb-data --fork --logpath ~/mongodb.log

# -----------------------------
# 4. MongoDB collections setup
# -----------------------------
echo "📊 Creating MongoDB collections..."

python db/mongo_setup.py

# -----------------------------
# 5. Final verification
# -----------------------------
echo "🔍 Verifying setup..."

# Check PostgreSQL tables
sudo -u postgres psql -d transpiler_db -c "\dt"

# Check MongoDB connection
python - <<EOF
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/")
print("MongoDB databases:", client.list_database_names())
EOF

echo "✅ Setup completed successfully!"
