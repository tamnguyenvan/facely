#!/bin/bash
# Facely Environment Setup Script

echo "=================================="
echo "Facely Environment Setup"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo ""
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Download models
echo ""
echo "Downloading models..."
python scripts/download_models.py

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p data
mkdir -p logs
echo "✓ Directories created"

# Initialize database
echo ""
echo "Initializing database..."
python scripts/init_db.py

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "To run Facely:"
echo "  1. Activate the virtual environment:"
echo "     source .venv/bin/activate"
echo "  2. Run the application:"
echo "     python main.py"
echo ""
echo "See QUICKSTART.md for more information."