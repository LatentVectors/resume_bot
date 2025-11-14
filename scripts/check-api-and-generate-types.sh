#!/bin/bash

# Check if API is running
API_URL="http://localhost:8000/api/health"

echo "Checking if API is running at $API_URL..."

# Try to reach the health endpoint
if curl -f -s "$API_URL" > /dev/null 2>&1; then
  echo "✓ API is running"
  echo "Generating types..."
  cd apps/web && npm run generate:types
else
  echo "✗ API is not running at $API_URL"
  echo ""
  echo "Please start the backend API first:"
  echo "  cd apps/api && npm run dev"
  echo ""
  echo "The API should be running on http://localhost:8000"
  echo ""
  exit 1
fi

