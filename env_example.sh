#!/usr/bin/env bash

# Check if .env exists
if [ ! -f .env ]; then
  echo ".env file not found!"
  exit 1
fi

# Create .env.example with values stripped
echo "Generating .env.example..."
sed -E 's/=.*/=/' .env > .env.example

echo ".env.example created successfully."
