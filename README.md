# 🏗️ AWS 3-Tier Infrastructure with Pulumi (Python)

This project provisions a **complete 3-tier AWS architecture** using **Pulumi (Python)**.  
It includes **networking, compute, security, and automation** for a **Flask CRUD application** hosted on private EC2 instances behind an **Application Load Balancer (ALB)**.  

---

## 📦 Architecture Overview

```
                ┌──────────────────────────────┐
                │          AWS Cloud           │
                │ ┌──────────────────────────┐ │
                │ │       VPC (10.0.0.0/16) │ │
                │ │ ┌────────────┐ ┌────────┐│ │
   Internet --->│ │ │ Public SN1 │ │ Pub SN2││ │
                │ │ │ Bastion EC2│ │ Bastion││ │
                │ │ └────┬───────┘ └────────┘│ │
                │ │      │  (via IGW)        │ │
                │ │   ┌───────────────┐      │ │
                │ │   │   ALB (HTTP)  │────┐ │ │
                │ │   └───────────────┘    │ │ │
                │ │ ┌────────────┐ ┌────────┐│ │
                │ │ │ Private SN1│ │Priv SN2││ │
                │ │ │ Flask EC2s │ │ Flask  ││ │
                │ │ └────────────┘ └────────┘│ │
                │ └──────────────────────────┘ │
                └──────────────────────────────┘
```

---

## ⚙️ Components

| Layer | Resource | Description |
|--------|-----------|-------------|
| **Network** | VPC, 2 public + 2 private subnets, IGW, NAT Gateway, Route Tables | Full 3-tier network setup |
| **Compute** | 2 Public + 2 Private EC2 | Public = Bastion, Private = Flask app |
| **Security** | SGs for ALB, Bastion, App EC2s | Port 22/80/5000 rules |
| **Load Balancer** | Application Load Balancer (ALB) | Forwards traffic to Flask app |
| **App** | Flask REST API | Simple CRUD API for demo |
| **IaC** | Pulumi (Python) | Declarative Infrastructure as Code |

---

## 🚀 Prerequisites

### 1️⃣ Install Required Tools
```bash
sudo apt install python3 python3-venv awscli -y
curl -fsSL https://get.pulumi.com | sh
pip install pulumi pulumi_aws
```

### 2️⃣ Configure AWS Credentials
```bash
aws configure
# or, if using multiple accounts
aws configure --profile myprofile
export AWS_PROFILE=myprofile
```

### 3️⃣ Create and Initialize Pulumi Stack
```bash
pulumi stack init dev
pulumi config set aws:region ap-southeast-1
```

---

## 🔑 SSH Key Setup for EC2 Access

### Step 1️⃣ — Create SSH Key Locally
```bash
mkdir -p ~/.ssh
cd ~/.ssh
ssh-keygen -t rsa -b 4096 -f pulumi-aws-key -N ""
```

This generates:
- `~/.ssh/pulumi-aws-key` → **private key**
- `~/.ssh/pulumi-aws-key.pub` → **public key**

### Step 2️⃣ — Configure Pulumi Key Pair Module
Your Pulumi code (`security/keypair.py`) should:
- Upload your public key to AWS as an EC2 Key Pair
- Store it as `pulumi-aws-key` in AWS

---

## 🌐 Network Validation: IGW and NAT Gateway

After deployment, verify that:
1. **Internet Gateway (IGW)** is attached to the **VPC**
2. **NAT Gateway** is created in **Public Subnet 1**
3. **Public Route Table** routes `0.0.0.0/0` to IGW
4. **Private Route Table** routes `0.0.0.0/0` to NAT Gateway

You can verify via:
```bash
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=<your-vpc-id>" --region ap-southeast-1
```

✅ Example routes:
```
Destination | Target
-------------|------------------
10.0.0.0/16  | local
0.0.0.0/0    | igw-xxxxxx  (for public)
0.0.0.0/0    | nat-xxxxxx  (for private)
```

---

## 💻 Connecting to EC2 Instances

### Step 1️⃣ — Connect to Public EC2 (Bastion)
```bash
chmod 400 ~/.ssh/pulumi-aws-key
ssh -i ~/.ssh/pulumi-aws-key ec2-user@<public-ec2-public-ip>
```

### Step 2️⃣ — Connect from Public → Private EC2
From inside your public EC2:
```bash
ssh -i ~/.ssh/pulumi-aws-key ec2-user@<private-ec2-private-ip>
```

> 💡 Tip: You can list all private EC2 IPs from Pulumi outputs:
```bash
pulumi stack output private_instance_1_private_ip
pulumi stack output private_instance_2_private_ip
```

If SSH to private EC2 fails:
- Ensure `app-ec2-sg` allows port 22 **from** `public-ec2-sg`
- Verify NAT Gateway & routing are working

---

## 🧱 Deploy Infrastructure

```bash
pulumi up
```

Pulumi will:
- Provision the VPC, subnets, gateways, security groups
- Launch EC2 instances and ALB
- Automatically run `user_data` to install Flask app

Once done, check:
```bash
pulumi stack output alb_dns
```

Then open:
```
http://<alb_dns_name>/
```

✅ Expected Output:
```json
{"service": "india-states-crud", "version": "v1"}
```

---

## 🧩 Troubleshooting: ALB Not Accessible or Instances Unhealthy

### 1️⃣ Check Flask App Logs
```bash
sudo cat /var/log/flask-setup.log
sudo systemctl status app.service
```

If you see:
```
ModuleNotFoundError: No module named 'flask'
```
→ pip wasn’t installed.  
Recreate EC2s after fixing user_data.

---

### 2️⃣ Ensure `user_data` Is Attached & Encoded

In `ec2_instances.py`:
```python
import base64

user_data=base64.b64encode(user_data_private.encode("utf-8")).decode("utf-8")
```

Recreate EC2s:
```bash
pulumi destroy --target aws:ec2/instance:Instance
pulumi up
```

---

### 3️⃣ Check Health Checks
Go to **EC2 → Target Groups → app-tg → Targets**  
✅ Status: `healthy`  
If unhealthy → Flask might not be bound to `0.0.0.0:5000`.

Fix:
```python
app.run(host='0.0.0.0', port=5000)
```

---

### 4️⃣ Verify Security Groups

| Group | Rule | Source |
|--------|------|--------|
| alb-sg | TCP 80 | 0.0.0.0/0 |
| public-ec2-sg | TCP 22 | 0.0.0.0/0 |
| app-ec2-sg | TCP 5000 | alb-sg |
| app-ec2-sg | TCP 22 | public-ec2-sg |

---

### 5️⃣ Verify Routing
```bash
aws ec2 describe-route-tables --region ap-southeast-1
```

Ensure:
- Public subnets → IGW
- Private subnets → NAT Gateway

---

### 6️⃣ Validate Cloud-Init Execution
On any private EC2:
```bash
sudo cat /var/log/cloud-init-output.log
sudo journalctl -u app.service -n 20 --no-pager
```

✅ Look for:
```
==== Flask app setup complete ====
```

---

## 🧼 Cleanup

When finished:
```bash
pulumi destroy
```

---

## ✅ Final Validation Checklist

| Check | Expected |
|--------|-----------|
| ALB DNS accessible | ✅ Returns JSON |
| Flask service active | ✅ systemctl active |
| `/var/log/flask-setup.log` exists | ✅ Yes |
| NAT Gateway active | ✅ Yes |
| IGW attached | ✅ Yes |
| Bastion SSH to private EC2 works | ✅ Yes |

---

## 🧾 Example Successful ALB Output

```
http://alb-xxxxxxxx.ap-southeast-1.elb.amazonaws.com/
```

Response:
```json
{"service": "india-states-crud", "version": "v1"}
```
