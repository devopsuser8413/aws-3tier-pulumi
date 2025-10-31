import pulumi_aws as aws

def create_security_groups(vpc_id):
    alb_sg = aws.ec2.SecurityGroup(
        "alb-sg",
        vpc_id=vpc_id,
        description="ALB Security Group",
        ingress=[aws.ec2.SecurityGroupIngressArgs(protocol="tcp", from_port=80, to_port=80, cidr_blocks=["0.0.0.0/0"])],
        egress=[aws.ec2.SecurityGroupEgressArgs(protocol="-1", from_port=0, to_port=0, cidr_blocks=["0.0.0.0/0"])],
        tags={"Name": "alb-sg"}
    )

    public_sg = aws.ec2.SecurityGroup(
        "public-ec2-sg",
        vpc_id=vpc_id,
        description="Public EC2 Security Group",
        ingress=[aws.ec2.SecurityGroupIngressArgs(protocol="tcp", from_port=22, to_port=22, cidr_blocks=["0.0.0.0/0"])],
        egress=[aws.ec2.SecurityGroupEgressArgs(protocol="-1", from_port=0, to_port=0, cidr_blocks=["0.0.0.0/0"])],
        tags={"Name": "public-ec2-sg"}
    )

    app_sg = aws.ec2.SecurityGroup(
        "app-ec2-sg",
        vpc_id=vpc_id,
        description="App EC2 Security Group",
        ingress=[aws.ec2.SecurityGroupIngressArgs(protocol="tcp", from_port=5000, to_port=5000, security_groups=[alb_sg.id])],
        egress=[aws.ec2.SecurityGroupEgressArgs(protocol="-1", from_port=0, to_port=0, cidr_blocks=["0.0.0.0/0"])],
        tags={"Name": "app-ec2-sg"}
    )

    return alb_sg, public_sg, app_sg
