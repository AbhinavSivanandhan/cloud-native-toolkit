#!/bin/bash
set -e

echo "🌍 Setting up Cloud Native Toolkit..."

# ----------- 🧱 Install Homebrew and Tools (macOS) -----------
if [[ "$OSTYPE" == "darwin"* ]]; then
  echo "🍺 Checking for Homebrew..."
  if ! command -v brew &>/dev/null; then
    echo "🔧 Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  fi

  echo "📦 Installing prerequisites via brew..."
  brew install awscli
  brew tap hashicorp/tap
  brew install hashicorp/tap/terraform
  brew install python@3.9
fi

# ----------- 🔐 AWS Credentials Setup -----------
echo "🔐 Make sure you’ve run: aws configure (to set credentials)"
aws sts get-caller-identity || {
  echo "❌ AWS credentials not found. Run 'aws configure' before continuing."
  exit 1
}

# ----------- 🐍 Python Virtual Environment Setup -----------
echo "🐍 Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

echo "📦 Installing Python dependencies..."
pip install --upgrade pip > /dev/null
pip install -r dashboards/cost_insights_ui/requirements.txt > /dev/null

# ----------- 🔨 Build Lambda ZIPs -----------
echo "📦 Building Lambda package for security guard..."
cd cloud-cost-insights/infra/lambda
bash build_lambda.sh
cd ../../../

# ----------- 🌍 Terraform Init & Apply -----------
echo "🚀 Initializing Terraform..."
cd cloud-cost-insights/infra
terraform init
terraform apply -auto-approve -var-file=secrets.auto.tfvars

# ----------- 📄 Export Terraform Output for Dashboard -----------
terraform output -json > ../../dashboards/cost_insights_ui/api_info.json

cd ../../

echo "✅ Setup complete! Run the API server using:"
echo ""
echo "   source .venv/bin/activate"
echo "   python dashboards/cost_insights_ui/app.py"
echo ""
echo "🎉 Done."
