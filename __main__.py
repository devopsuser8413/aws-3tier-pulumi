import pulumi
import pulumi_aws as aws
from pulumi import Config, ResourceOptions
from typing import List

cfg = Config()
vpc_cidr = cfg.get("vpcCidr") or "10.0.0.0/16"
public_cidrs: List[str] = cfg.get_object("publicCidrs") or ["10.0.1.0/24", "10.0.2.0/24"]
private_cidrs: List[str] = cfg.get_object("privateCidrs") or ["10.0.11.0/24", "10.0.12.0/24"]
instance_type = cfg.get("instanceType") or "t3.micro"
key_name = cfg.get("keyName")  # optional: existing EC2 key pair name
ssh_cidr = cfg.get("sshCidr") or "0.0.0.0/0"  # for demo; restrict in production
per_subnet_instance_count = int(cfg.get("perSubnetInstanceCount") or 2)  # 2 on each subnet (public & private)

# --------------- VPC & Networking ---------------
vpc = aws.ec2.Vpc(
    "vpc",
    cidr_block=vpc_cidr,
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={"Name": "pulumi-3tier-vpc"},
)

igw = aws.ec2.InternetGateway("igw", vpc_id=vpc.id, tags={"Name": "pulumi-igw"})

# Two AZs for HA
azs = aws.get_availability_zones(state="available").names[:2]

public_subnets = []
private_subnets = []
public_route_tables = []
private_route_tables = []

for i, cidr in enumerate(public_cidrs):
    sn = aws.ec2.Subnet(
        f"public-subnet-{i+1}",
        vpc_id=vpc.id,
        cidr_block=cidr,
        availability_zone=azs[i % len(azs)],
        map_public_ip_on_launch=True,
        tags={"Name": f"public-{i+1}"},
    )
    public_subnets.append(sn)

for i, cidr in enumerate(private_cidrs):
    sn = aws.ec2.Subnet(
        f"private-subnet-{i+1}",
        vpc_id=vpc.id,
        cidr_block=cidr,
        availability_zone=azs[i % len(azs)],
        map_public_ip_on_launch=False,
        tags={"Name": f"private-{i+1}"},
    )
    private_subnets.append(sn)

# Public route table -> IGW
for i, sn in enumerate(public_subnets):
    rt = aws.ec2.RouteTable(
        f"public-rt-{i+1}", vpc_id=vpc.id, tags={"Name": f"public-rt-{i+1}"}
    )
    aws.ec2.Route(
        f"public-rt-{i+1}-default",
        route_table_id=rt.id,
        destination_cidr_block="0.0.0.0/0",
        gateway_id=igw.id,
    )
    aws.ec2.RouteTableAssociation(
        f"public-rta-{i+1}",
        subnet_id=sn.id,
        route_table_id=rt.id,
    )
    public_route_tables.append(rt)

# Single NAT Gateway in the first public subnet (user asked for one NGW)

nat_eip = aws.ec2.Eip("nat-eip", domain="vpc")

nat_gw = aws.ec2.NatGateway(
    "nat-gw",
    subnet_id=public_subnets[0].id,
    allocation_id=nat_eip.allocation_id,
    tags={"Name": "pulumi-nat-gw"},
)

# Private route tables -> NAT GW
for i, sn in enumerate(private_subnets):
    rt = aws.ec2.RouteTable(
        f"private-rt-{i+1}", vpc_id=vpc.id, tags={"Name": f"private-rt-{i+1}"}
    )
    aws.ec2.Route(
        f"private-rt-{i+1}-default",
        route_table_id=rt.id,
        destination_cidr_block="0.0.0.0/0",
        nat_gateway_id=nat_gw.id,
    )
    aws.ec2.RouteTableAssociation(
        f"private-rta-{i+1}",
        subnet_id=sn.id,
        route_table_id=rt.id,
    )
    private_route_tables.append(rt)

# --------------- Security Groups ---------------
# ALB SG: allow inbound 80 from anywhere; egress to app SG
alb_sg = aws.ec2.SecurityGroup(
    "alb-sg",
    vpc_id=vpc.id,
    description="ALB SG",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp", from_port=80, to_port=80, cidr_blocks=["0.0.0.0/0"]
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1", from_port=0, to_port=0, cidr_blocks=["0.0.0.0/0"]
        )
    ],
    tags={"Name": "alb-sg"},
)

# Bastion/Web SG for public instances (SSH allowed from configured CIDR, HTTP optional)
public_ec2_sg = aws.ec2.SecurityGroup(
    "public-ec2-sg",
    vpc_id=vpc.id,
    description="Public EC2 SG (bastion/web)",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp", from_port=22, to_port=22, cidr_blocks=[ssh_cidr]
        ),
        # Uncomment to expose a web server on public instances if needed
        # aws.ec2.SecurityGroupIngressArgs(
        #     protocol="tcp", from_port=80, to_port=80, cidr_blocks=["0.0.0.0/0"]
        # ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1", from_port=0, to_port=0, cidr_blocks=["0.0.0.0/0"]
        )
    ],
    tags={"Name": "public-ec2-sg"},
)

# App SG for private instances: allow port 5000 from ALB SG, SSH from public EC2 SG
app_ec2_sg = aws.ec2.SecurityGroup(
    "app-ec2-sg",
    vpc_id=vpc.id,
    description="Private app EC2 SG",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp", from_port=5000, to_port=5000, security_groups=[alb_sg.id]
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp", from_port=22, to_port=22, security_groups=[public_ec2_sg.id]
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1", from_port=0, to_port=0, cidr_blocks=["0.0.0.0/0"]
        )
    ],
    tags={"Name": "app-ec2-sg"},
)

# --------------- AMI Lookup ---------------
ami = aws.ec2.get_ami(
    owners=["137112412989"],  # Amazon Linux 2023 owner
    most_recent=True,
    filters=[
        aws.ec2.GetAmiFilterArgs(name="name", values=["al2023-ami-*-x86_64"]),
        aws.ec2.GetAmiFilterArgs(name="architecture", values=["x86_64"]),
        aws.ec2.GetAmiFilterArgs(name="root-device-type", values=["ebs"]),
        aws.ec2.GetAmiFilterArgs(name="virtualization-type", values=["hvm"]),
    ],
)

# --------------- User data for private app servers ---------------
# Simple Flask CRUD app (SQLite) for Indian states: population, religions, languages
app_user_data = """#!/bin/bash
set -eux
# Basic deps
dnf update -y || yum update -y || true
# Python3 is default on AL2023
python3 -m pip install --upgrade pip
python3 -m pip install flask flask-cors gunicorn sqlalchemy pydantic

cat >/opt/app.py <<'PY'
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

app = Flask(__name__)
CORS(app)
engine = create_engine('sqlite:////opt/states.db', echo=False)
Base = declarative_base()

class State(Base):
    __tablename__ = 'states'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
    population = Column(Integer, nullable=False)
    religions = Column(String(512), nullable=False)   # comma-separated
    languages = Column(String(512), nullable=False)   # comma-separated

Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

@app.get('/states')
def list_states():
    with SessionLocal() as s:
        data = s.query(State).all()
        return jsonify([
            {"id": x.id, "name": x.name, "population": x.population,
             "religions": x.religions.split(','), "languages": x.languages.split(',')}
            for x in data
        ])

@app.post('/states')
def create_state():
    body = request.get_json(force=True)
    with SessionLocal() as s:
        st = State(
            name=body['name'],
            population=int(body['population']),
            religions=','.join(body.get('religions', [])),
            languages=','.join(body.get('languages', [])),
        )
        s.add(st); s.commit(); s.refresh(st)
        return jsonify({"id": st.id}), 201

@app.put('/states/<int:id>')
def update_state(id:int):
    body = request.get_json(force=True)
    with SessionLocal() as s:
        st = s.get(State, id)
        if not st:
            return jsonify({"error": "not found"}), 404
        st.name = body.get('name', st.name)
        st.population = int(body.get('population', st.population))
        if 'religions' in body: st.religions = ','.join(body['religions'])
        if 'languages' in body: st.languages = ','.join(body['languages'])
        s.commit(); s.refresh(st)
        return jsonify({"ok": True})

@app.delete('/states/<int:id>')
def delete_state(id:int):
    with SessionLocal() as s:
        st = s.get(State, id)
        if not st:
            return jsonify({"error": "not found"}), 404
        s.delete(st); s.commit()
        return jsonify({"ok": True})

@app.get('/')
def root():
    return jsonify({"service": "india-states-crud", "version": "v1"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
PY

cat >/etc/systemd/system/app.service <<'SVC'
[Unit]
Description=Gunicorn for India States CRUD
After=network.target

[Service]
User=root
ExecStart=/usr/bin/python3 -m gunicorn -w 2 -b 0.0.0.0:5000 app:app
WorkingDirectory=/opt
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SVC

systemctl daemon-reload
systemctl enable --now app.service
"""

# --------------- User data for public (bastion/web) instances ---------------
public_user_data = """#!/bin/bash
set -eux
# Install SSM Agent for secure access (optional)
if ! rpm -q amazon-ssm-agent >/dev/null 2>&1; then
  dnf install -y https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm || true
  systemctl enable --now amazon-ssm-agent || true
fi
# Tiny landing page (optional)
mkdir -p /var/www/html
cat >/var/www/html/index.html <<HTML
<html><body><h1>Pulumi 3-Tier Demo</h1><p>ALB fronts private app on port 80.</p></body></html>
HTML
"""

# --------------- IAM role (optional) to allow SSM ---------------
assume_role_doc = aws.iam.get_policy_document(
    statements=[aws.iam.GetPolicyDocumentStatementArgs(
        actions=["sts:AssumeRole"],
        principals=[aws.iam.GetPolicyDocumentStatementPrincipalArgs(type="Service", identifiers=["ec2.amazonaws.com"])],
    )]
)

role = aws.iam.Role("ec2-role", assume_role_policy=assume_role_doc.json)
aws.iam.RolePolicyAttachment(
    "ssm-core",
    role=role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
)

instance_profile = aws.iam.InstanceProfile("ec2-instance-profile", role=role.name)

# --------------- EC2 Instances ---------------
public_instances = []
private_instances = []

for i, sn in enumerate(public_subnets):
    for n in range(per_subnet_instance_count):
        inst = aws.ec2.Instance(
            f"public-ec2-{i+1}-{n+1}",
            ami=ami.id,
            instance_type=instance_type,
            subnet_id=sn.id,
            vpc_security_group_ids=[public_ec2_sg.id],
            key_name=key_name,
            associate_public_ip_address=True,
            user_data=public_user_data,
            iam_instance_profile=instance_profile.name,
            tags={"Name": f"public-{i+1}-{n+1}"},
        )
        public_instances.append(inst)

for i, sn in enumerate(private_subnets):
    for n in range(per_subnet_instance_count):
        inst = aws.ec2.Instance(
            f"app-ec2-{i+1}-{n+1}",
            ami=ami.id,
            instance_type=instance_type,
            subnet_id=sn.id,
            vpc_security_group_ids=[app_ec2_sg.id],
            key_name=key_name,
            associate_public_ip_address=False,
            user_data=app_user_data,
            iam_instance_profile=instance_profile.name,
            tags={"Name": f"app-{i+1}-{n+1}"},
        )
        private_instances.append(inst)

# --------------- Application Load Balancer ---------------
alb = aws.lb.LoadBalancer(
    "alb",
    load_balancer_type="application",
    internal=False,
    security_groups=[alb_sg.id],
    subnets=[sn.id for sn in public_subnets],
    tags={"Name": "pulumi-alb"},
)

tg = aws.lb.TargetGroup(
    "app-tg",
    port=5000,
    protocol="HTTP",
    target_type="instance",
    vpc_id=vpc.id,
    health_check=aws.lb.TargetGroupHealthCheckArgs(path="/", matcher="200-399", interval=30),
)

# Attach each private instance to the Target Group
for i, inst in enumerate(private_instances):
    aws.lb.TargetGroupAttachment(
        f"tg-attach-{i+1}",
        target_group_arn=tg.arn,
        target_id=inst.id,
        port=5000,
    )

listener = aws.lb.Listener(
    "http-listener",
    load_balancer_arn=alb.arn,
    port=80,
    protocol="HTTP",
    default_actions=[aws.lb.ListenerDefaultActionArgs(type="forward", target_group_arn=tg.arn)],
)

# --------------- Useful Outputs ---------------
pulumi.export("vpcId", vpc.id)
pulumi.export("publicSubnetIds", [sn.id for sn in public_subnets])
pulumi.export("privateSubnetIds", [sn.id for sn in private_subnets])
pulumi.export("albDnsName", alb.dns_name)
pulumi.export("publicInstanceIds", [i.id for i in public_instances])
pulumi.export("privateInstanceIds", [i.id for i in private_instances])
