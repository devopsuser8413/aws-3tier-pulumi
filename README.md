# 🏗️ Pulumi AWS 3-Tier Infrastructure with Flask CRUD Application

This project uses **Pulumi (Python)** to provision a full **3-tier architecture** on **AWS**, hosting a small Flask CRUD API that maintains information about **Indian states, population, religions, and languages**.

---

## 🧱 Architecture Overview

### 🔹 Components
| Tier | Components | Description |
|------|-------------|--------------|
| **Network Layer** | VPC, 2 Public Subnets, 2 Private Subnets, IGW, NAT Gateway | Provides isolated networking across AZs |
| **Compute Layer** | 2 EC2s in each public and private subnet | Public = bastion hosts; Private = Flask app servers |
| **Load Balancer Layer** | Application Load Balancer (ALB) | Routes HTTP traffic to private EC2s (port 5000) |
| **Security** | Security Groups | Restrict SSH/HTTP between tiers |
| **App** | Flask + Gunicorn + SQLite | Simple CRUD app for states data |

---

## ⚙️ Prerequisites

Before you begin, ensure you have:

- 🐍 **Python 3.8+** installed
- ☁️ **AWS CLI** configured with access keys
- 💻 **Pulumi CLI** installed  
  [Install Guide →](https://www.pulumi.com/docs/install/)
- 🧰 **Git** installed
- (Optional) **Virtual environment** for Python

---

## 📂 Project Structure

```
aws-3tier-pulumi/
├── Pulumi.yaml             # Project metadata
├── Pulumi.dev.yaml         # Stack configuration (auto-generated)
├── __main__.py             # Main Pulumi Python code
├── requirements.txt        # Pulumi dependencies
├── .gitignore
└── README.md
```

---

## 🪜 Step-by-Step Deployment Guide

### 1️⃣ Clone the repository
```bash
git clone https://github.com/<your-username>/aws-3tier-pulumi.git
cd aws-3tier-pulumi
```

---

### 2️⃣ Set up a Python virtual environment
```bash
python3 -m venv venv
source venv/bin/activate      # On macOS/Linux
# or
venv\Scripts\activate         # On Windows
```

---

### 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

---

### 4️⃣ Configure Pulumi
Initialize and configure your Pulumi stack:

```bash
pulumi stack init dev       # (or select an existing stack)
pulumi config set aws:region ap-south-1
pulumi config set vpcCidr 10.0.0.0/16
pulumi config set --path publicCidrs '["10.0.1.0/24","10.0.2.0/24"]'
pulumi config set --path privateCidrs '["10.0.11.0/24","10.0.12.0/24"]'
pulumi config set instanceType t3.micro
pulumi config set perSubnetInstanceCount 2
pulumi config set sshCidr 0.0.0.0/0
# Optional if you have an EC2 key pair
# pulumi config set keyName my-keypair
```

✅ Check your settings:
```bash
pulumi config
```

---

### 5️⃣ Authenticate with AWS
Make sure your AWS CLI is configured:
```bash
aws configure
```
or use an existing profile:
```bash
export AWS_PROFILE=myprofile
```

Test credentials:
```bash
aws sts get-caller-identity
```

---

### 6️⃣ Deploy the stack
Run:
```bash
pulumi up
```

Pulumi will show a preview of all AWS resources.  
Type `yes` to confirm creation.

---

### 7️⃣ View Outputs
After deployment completes, note the output values:
```
Outputs:
  albDnsName : "pulumi-alb-xxxxx.ap-south-1.elb.amazonaws.com"
```

---

## 🌐 Access the Application

Open in browser:
```
http://<albDnsName>/
```

You should see:
```json
{"service": "india-states-crud", "version": "v1"}
```

---

## 🧪 Test the CRUD API

Use **curl** or **Postman** to test the endpoints.

### ➕ Create a State
```bash
curl -X POST http://<albDnsName>/states   -H "Content-Type: application/json"   -d '{
        "name": "Karnataka",
        "population": 61095297,
        "religions": ["Hinduism","Islam","Christianity","Jainism"],
        "languages": ["Kannada","Urdu","Hindi"]
      }'
```

### 📋 List All States
```bash
curl http://<albDnsName>/states
```

### ✏️ Update a State
```bash
curl -X PUT http://<albDnsName>/states/1   -H "Content-Type: application/json"   -d '{"population": 65000000}'
```

### ❌ Delete a State
```bash
curl -X DELETE http://<albDnsName>/states/1
```

---

## 🔍 Troubleshooting

### ❗ ALB not reachable
- Wait for ALB to become **Active**
- Ensure ALB SG allows port 80 from `0.0.0.0/0`
- Ensure private EC2 SG allows port 5000 from ALB SG

### ❗ SSM Agent not online
- Confirm NAT Gateway is available  
- Private route table should point `0.0.0.0/0 → NAT Gateway`
- Restart agent:
  ```bash
  sudo systemctl restart amazon-ssm-agent
  ```

---

## 🧼 Cleanup

To delete all AWS resources created by this project:
```bash
pulumi destroy
```

Then remove the stack record:
```bash
pulumi stack rm dev
```

---

## 🧠 Notes & Enhancements

| Enhancement | Description |
|--------------|-------------|
| 🗄️ Use RDS instead of SQLite | Store data in MySQL/PostgreSQL via AWS RDS |
| ⚖️ Auto Scaling | Add EC2 Auto Scaling Group with Launch Template |
| 🔒 HTTPS | Add ACM certificate + ALB HTTPS listener |
| 🏠 DNS | Map ALB to a custom Route53 domain |
| ⚙️ CI/CD | Use GitHub Actions or GitLab CI for automated deploys |

---

## 📜 License
MIT License © 2025 [Your Name]

---

## 🤝 Contributing
Pull requests are welcome!  
For major changes, please open an issue first to discuss what you’d like to change.

---

## 🧰 Helpful Resources
- [Pulumi AWS Docs](https://www.pulumi.com/registry/packages/aws/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [AWS VPC Guide](https://docs.aws.amazon.com/vpc/)
