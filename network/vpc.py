import pulumi_aws as aws

def create_network():
    # Create the VPC
    vpc = aws.ec2.Vpc(
        "vpc",
        cidr_block="10.0.0.0/16",
        enable_dns_hostnames=True,
        enable_dns_support=True,
        tags={"Name": "pulumi-vpc"}
    )

    # Create Internet Gateway
    igw = aws.ec2.InternetGateway("igw", vpc_id=vpc.id)

    # Availability Zones
    azs = aws.get_availability_zones().names[:2]

    # Public and Private Subnets
    public_subnets = []
    private_subnets = []

    for i, cidr in enumerate(["10.0.1.0/24", "10.0.2.0/24"]):
        public_subnets.append(
            aws.ec2.Subnet(
                f"public-{i+1}",
                vpc_id=vpc.id,
                cidr_block=cidr,
                map_public_ip_on_launch=True,
                availability_zone=azs[i],
                tags={"Name": f"public-{i+1}"}
            )
        )

    for i, cidr in enumerate(["10.0.11.0/24", "10.0.12.0/24"]):
        private_subnets.append(
            aws.ec2.Subnet(
                f"private-{i+1}",
                vpc_id=vpc.id,
                cidr_block=cidr,
                map_public_ip_on_launch=False,
                availability_zone=azs[i],
                tags={"Name": f"private-{i+1}"}
            )
        )

    # NAT Gateway and Elastic IP
    nat_eip = aws.ec2.Eip("nat-eip", domain="vpc")
    nat_gw = aws.ec2.NatGateway(
        "nat-gw",
        subnet_id=public_subnets[0].id,
        allocation_id=nat_eip.allocation_id,
        tags={"Name": "nat-gw"}
    )

    # Public Route Table (Internet-facing)
    public_rt = aws.ec2.RouteTable(
        "public-rt",
        vpc_id=vpc.id,
        routes=[
            aws.ec2.RouteTableRouteArgs(
                cidr_block="0.0.0.0/0",
                gateway_id=igw.id
            )
        ],
        tags={"Name": "public-rt"}
    )

    # Associate public subnets with public route table
    for i, subnet in enumerate(public_subnets):
        aws.ec2.RouteTableAssociation(
            f"public-rta-{i+1}",
            subnet_id=subnet.id,
            route_table_id=public_rt.id
        )

    # Private Route Table (NAT Gateway for outbound)
    private_rt = aws.ec2.RouteTable(
        "private-rt",
        vpc_id=vpc.id,
        routes=[
            aws.ec2.RouteTableRouteArgs(
                cidr_block="0.0.0.0/0",
                nat_gateway_id=nat_gw.id
            )
        ],
        tags={"Name": "private-rt"}
    )

    # Associate private subnets with private route table
    for i, subnet in enumerate(private_subnets):
        aws.ec2.RouteTableAssociation(
            f"private-rta-{i+1}",
            subnet_id=subnet.id,
            route_table_id=private_rt.id
        )

    # Return resources
    return vpc, public_subnets, private_subnets, igw, nat_gw
