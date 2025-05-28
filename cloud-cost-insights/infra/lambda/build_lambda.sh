#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "🔧 Cleaning old builds..."
rm -rf build lambda_security.zip lambda_governance.zip

echo "📦 Installing shared dependencies..."
python3 -m pip install -r requirements.txt -t build/

# --- Build Security Guard ---
echo "🔐 Building Security Guard Lambda..."
cp security_guard.py build/
cd build
zip -r ../lambda_security.zip .
rm security_guard.py
cd ..

# --- Build IaC Refactor ---
echo "🛠️ Building IaC Refactor Lambda..."
cp governance_copilot.py build/
cd build
zip -r ../lambda_governance.zip .
rm governance_copilot.py
cd ..

echo "✅ All Lambda packages built successfully."
