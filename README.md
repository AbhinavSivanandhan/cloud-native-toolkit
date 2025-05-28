Instructions for **setting up the AWS IAM user**, and clear onboarding for someone cloning this project from scratch:

---

## 🧠 Cloud Native Toolkit

Cloud visibility & cost governance for solo builders, startups, and lean infra teams.
Scan AWS accounts for **cost**, **security**, and **infra drift** in one click.

---

## 🔧 Setup Instructions

### ✅ Prerequisites (I've provided for MacOS but feel free to skip this section, you can do this by removing the instructions from setup script)

You need the following tools installed:

| Tool            | Install Command (macOS)                                                                           |
| --------------- | ------------------------------------------------------------------------------------------------- |
| **Homebrew**    | `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"` |
| **Terraform**   | `brew tap hashicorp/tap && brew install hashicorp/tap/terraform`                                  |
| **AWS CLI**     | `brew install awscli`                                                                             |
| **Python 3.9+** | `brew install python@3.9` and set alias if needed with `alias python=python3.9`                   |

After that:

```bash
python3.9 --version
terraform -version
aws --version
```

---

### 🔐 AWS Credentials

1. **Login to AWS Console**
   👉 [AWS Console](https://333107834549.signin.aws.amazon.com/console)
   User: `cloud-toolkit-admin`
   *(Password stored in Google Password Manager or in your `.env`)*

2. **Configure local AWS credentials**
   Run:

   ```bash
   aws configure
   ```

   Enter:

   * Access Key ID
   * Secret Access Key
   * Region: `us-east-1`
   * Output format: `json`

This creates `~/.aws/credentials` and `~/.aws/config` automatically.

---

## 🚀 Project Setup

Clone the repo and run:

```bash
bash setup.sh
```

This does everything:

* Builds required Lambda packages
* Deploys all infra via Terraform
* Generates API info
* Prepares for dashboard API

Make sure `cloud-cost-insights/infra/secrets.auto.tfvars` exists:

```hcl
sonar_api_key = "your_perplexity_sonar_api_key"
```

---

## 🧠 Features

| Module                          | What It Does                                |
| ------------------------------- | ------------------------------------------- |
| 💰 **Cost Insights**            | Daily cost breakdown by service             |
| 🧹 **Resource Scanner**         | Detects unused EC2, EBS, and more           |
| 🛡️ **Security Insights Agent** | Flags risky IAM, ports, and S3 settings     |
| 🤖 **Infra Autopilot**          | Auto-stop EC2, archive logs monthly         |
| 📉 **AI Summary (Sonar)**       | Natural language cost + risk analysis       |
| 🕒 **Time Machine Mode**        | “Show me infra last Friday” *(coming soon)* |

---

## 👤 IAM User Info

The **cloud-toolkit-admin** user has:

* Permissions:

  * `AdministratorAccess`
  * `AWSBillingReadOnlyAccess`
  * Custom Policy: `CloudVisibilityFullAccess`
* Console access (not via AWS SSO or Identity Center)
* Project tag: `Project: cloud-native-toolkit`
* Can be used safely instead of root account

---

## 🧪 Run API Server

From the root:

```bash
source .venv/bin/activate
python dashboards/cost_insights_ui/app.py
```

You can query endpoints like `/summary`, `/security`, `/costs`.

---

## 🧼 Destroy Resources

```bash
make destroy
```

This runs `terraform destroy` and deletes all infra.

