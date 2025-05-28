#!/bin/bash

echo "🚀 Building MCP Sonar server..."
docker build -t mcp/perplexity-ask .

echo "🚀 Running MCP on port 5005..."
docker run --rm --name mcp-sonar -p 5005:5005 --env-file .env mcp/perplexity-ask

# give this file 'chmod +x mcp/start.sh'. also start docker daemon
#then do 'mcp % ./start.sh' to run it
