# 🏗️ Modular Pulumi AWS 3-Tier Infrastructure (ap-southeast-1)

This project provisions a **3-tier AWS architecture** using **Pulumi (Python)** in a **modular structure**.  
It also deploys a simple **Flask CRUD Application** to manage Indian state data (population, religion, and languages).

---

## 🧱 Architecture Overview

| Tier | Components | Description |
|------|-------------|--------------|
| **Network Layer** | VPC, 2 Public Subnets, 2 Private Subnets, IGW, NAT Gateway | Provides secure and scalable networking |
| **Compute Layer** | EC2 Instances (Public & Private) | Hosts Flask CRUD application and bastion nodes |
| **Load Balancer Layer** | Application Load Balancer (ALB) | Routes traffic to private EC2 app instances |
| **Security Layer** | Security Groups | Enforces access control between tiers |

---

## ⚙️ Prerequisites

Ensure you have the following installed:

- **Python 3.8+**
- **Pulumi CLI** → [Install Guide](https://www.pulumi.com/docs/install/)
- **AWS CLI** configured with valid credentials (`aws configure`)
- **Git** installed

---

## 📂 Project Structure

```
aws-3tier-pulumi-modular/
├── Pulumi.yaml
├── requirements.txt
├── __main__.py
├── network/
│   └── vpc.py
├── security/
│   └── security_groups.py
├── compute/
│   └── ec2_instances.py
├── loadbalancer/
│   └── alb.py
└── app/
    └── user_data.py
```

---

## 🪜 Step-by-Step Deployment

### 1️⃣ Create and Activate a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate      # macOS/Linux
# or
venv\Scripts\activate       # Windows
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Initialize Pulumi Stack

```bash
pulumi stack init dev
pulumi config set aws:region ap-southeast-1
```

### 4️⃣ Deploy Infrastructure

```bash
pulumi up
```

Confirm with `yes` when prompted.  
Pulumi will provision all required AWS resources.

### 5️⃣ View Outputs

After deployment completes, note key outputs:

```
Outputs:
  vpc_id  : vpc-xxxxxxxxxxxx
  alb_dns : pulumi-alb-xxxx.ap-southeast-1.elb.amazonaws.com
```

---

## 🌐 Access the Flask Application

Open the ALB DNS name in a browser:

```
http://<alb_dns_name>/
```

Expected Response:
```json
{"service": "india-states-crud", "version": "v1"}
```

---

## 🧪 Test API Endpoints (Using cURL)

### ➕ Create a State
```bash
curl -X POST http://<alb_dns_name>/states   -H "Content-Type: application/json"   -d '{
        "name": "Karnataka",
        "population": 61095297,
        "religions": ["Hinduism","Islam","Christianity"],
        "languages": ["Kannada","Urdu","Hindi"]
      }'
```

### 📋 Get All States
```bash
curl http://<alb_dns_name>/states
```

### ✏️ Update a State
```bash
curl -X PUT http://<alb_dns_name>/states/1   -H "Content-Type: application/json"   -d '{"population": 65000000}'
```

### ❌ Delete a State
```bash
curl -X DELETE http://<alb_dns_name>/states/1
```

---

## 🧰 Troubleshooting

| Issue | Possible Cause | Fix |
|--------|----------------|-----|
| ALB not reachable | ALB still provisioning or wrong SG rules | Wait a few minutes, verify ALB SG inbound port 80 |
| Instances Unhealthy | Flask not running / Health check path | Ensure app runs on port 5000 and returns HTTP 200 for `/` |
| SSM Agent not online | No NAT or SSM endpoint | Check NAT Gateway and private route tables |
| Pulumi error | Missing dependencies | Run `pip install -r requirements.txt` |

---

## 🧼 Cleanup Resources

To destroy all AWS resources:
```bash
pulumi destroy
```

To remove the Pulumi stack entirely:
```bash
pulumi stack rm dev
```

---

## 🧠 Enhancements

| Feature | Description |
|----------|--------------|
| Use RDS instead of SQLite | For persistent database storage |
| Enable HTTPS | Add ACM SSL certificate and ALB HTTPS listener |
| CI/CD Pipeline | Deploy automatically using GitHub Actions |
| Route53 Integration | Map ALB to a custom domain |
| Auto Scaling | Add EC2 Auto Scaling Group with Launch Template |

---

## 🧾 License

MIT License © 2025 [Your Name]

---

## 🧩 Helpful References
- [Pulumi AWS Docs](https://www.pulumi.com/registry/packages/aws/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [AWS VPC Docs](https://docs.aws.amazon.com/vpc/)
