#!/bin/bash
set -e

cd "$(dirname "$0")"

# Clean old build
rm -rf build lambda_security.zip

# Install dependencies
python3 -m pip install -r requirements.txt -t build/

# Add your source code
cp security_guard.py build/

# Create zip file
cd build
zip -r ../lambda_security.zip .
#(.venv) abhinavsivanandhan@Abhinavs-MacBook-Pro lambda % ./cloud-cost-insights/infra/lambda/build_lambda.sh
