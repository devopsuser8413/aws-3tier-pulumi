import pulumi_aws as aws

def create_security_groups(vpc_id):
    # ------------------------
    # ALB Security Group
    # ------------------------
    alb_sg = aws.ec2.SecurityGroup(
        "alb-sg",
        vpc_id=vpc_id,
        description="Allow HTTP from anywhere to ALB",
        ingress=[
            aws.ec2.SecurityGroupIngressArgs(
                protocol="tcp",
                from_port=80,
                to_port=80,
                cidr_blocks=["0.0.0.0/0"]
            )
        ],
        egress=[
            aws.ec2.SecurityGroupEgressArgs(
                protocol="-1",
                from_port=0,
                to_port=0,
                cidr_blocks=["0.0.0.0/0"]
            )
        ],
        tags={"Name": "alb-sg"}
    )

    # ------------------------
    # Public EC2 Security Group (Bastion)
    # ------------------------
    public_sg = aws.ec2.SecurityGroup(
        "public-ec2-sg",
        vpc_id=vpc_id,
        description="Allow SSH from the internet for Bastion hosts",
        ingress=[
            aws.ec2.SecurityGroupIngressArgs(
                protocol="tcp",
                from_port=22,
                to_port=22,
                cidr_blocks=["0.0.0.0/0"]  # Allow SSH from anywhere for testing
                # For production, replace with your IP: e.g. ["203.0.113.45/32"]
            )
        ],
        egress=[
            aws.ec2.SecurityGroupEgressArgs(
                protocol="-1",
                from_port=0,
                to_port=0,
                cidr_blocks=["0.0.0.0/0"]
            )
        ],
        tags={"Name": "public-ec2-sg"}
    )

    # ------------------------
    # Private EC2 Security Group (Application Layer)
    # ------------------------
    app_sg = aws.ec2.SecurityGroup(
        "app-ec2-sg",
        vpc_id=vpc_id,
        description="Allow HTTP from ALB and SSH from Bastion",
        ingress=[
            # Allow HTTP (Flask) from ALB
            aws.ec2.SecurityGroupIngressArgs(
                protocol="tcp",
                from_port=5000,
                to_port=5000,
                security_groups=[alb_sg.id]
            ),
            # ✅ Allow SSH (22) only from Bastion/Public SG
            aws.ec2.SecurityGroupIngressArgs(
                protocol="tcp",
                from_port=22,
                to_port=22,
                security_groups=[public_sg.id]
            ),
        ],
        egress=[
            aws.ec2.SecurityGroupEgressArgs(
                protocol="-1",
                from_port=0,
                to_port=0,
                cidr_blocks=["0.0.0.0/0"]
            )
        ],
        tags={"Name": "app-ec2-sg"}
    )

    return alb_sg, public_sg, app_sg
