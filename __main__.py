import pulumi
import pulumi_aws as aws
from network.vpc import create_network
from security.security_groups import create_security_groups
from compute.ec2_instances import create_instances
from loadbalancer.alb import create_alb
from app.user_data import get_user_data_public, get_user_data_private

# Network
vpc, public_subnets, private_subnets, igw, nat_gw = create_network()

# Security Groups
alb_sg, public_sg, app_sg = create_security_groups(vpc.id)

# AMI lookup
ami = aws.ec2.get_ami(
    owners=["137112412989"],
    most_recent=True,
    filters=[aws.ec2.GetAmiFilterArgs(name="name", values=["al2023-ami-*-x86_64"])]
)

# EC2 Instances
pub_instances, priv_instances = create_instances(
    ami.id, "t3.micro", public_subnets, private_subnets,
    public_sg, app_sg, get_user_data_public(), get_user_data_private()
)

# Load Balancer
alb, tg, listener = create_alb(vpc.id, public_subnets, alb_sg, priv_instances)

# Outputs
pulumi.export("vpc_id", vpc.id)
pulumi.export("alb_dns", alb.dns_name)
