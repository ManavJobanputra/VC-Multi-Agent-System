#!/bin/bash

echo "=== VC Multi-Agent System Setup ==="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Please install Node.js 20+ first."
    exit 1
fi

echo "Setting up backend..."
cd backend

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Backend setup complete!"

echo "Setting up frontend..."
cd ../frontend/vc-frontend

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
pnpm install

echo "Frontend setup complete!"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To start the system:"
echo "1. Start Qdrant database (if running locally)"
echo "2. In one terminal, run: cd backend && python main.py"
echo "3. In another terminal, run: cd frontend/vc-frontend && pnpm run dev --host"
echo ""
echo "The system will be available at:"
echo "- Backend: http://localhost:5000"
echo "- Frontend: http://localhost:5173"

