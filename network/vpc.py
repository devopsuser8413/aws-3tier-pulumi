import pulumi_aws as aws

def create_network():
    vpc = aws.ec2.Vpc("vpc", cidr_block="10.0.0.0/16", enable_dns_hostnames=True, enable_dns_support=True, tags={"Name": "pulumi-vpc"})
    igw = aws.ec2.InternetGateway("igw", vpc_id=vpc.id)

    azs = aws.get_availability_zones().names[:2]

    public_subnets = []
    private_subnets = []

    for i, cidr in enumerate(["10.0.1.0/24", "10.0.2.0/24"]):
        public_subnets.append(aws.ec2.Subnet(
            f"public-{i+1}",
            vpc_id=vpc.id,
            cidr_block=cidr,
            map_public_ip_on_launch=True,
            availability_zone=azs[i],
            tags={"Name": f"public-{i+1}"}
        ))

    for i, cidr in enumerate(["10.0.11.0/24", "10.0.12.0/24"]):
        private_subnets.append(aws.ec2.Subnet(
            f"private-{i+1}",
            vpc_id=vpc.id,
            cidr_block=cidr,
            map_public_ip_on_launch=False,
            availability_zone=azs[i],
            tags={"Name": f"private-{i+1}"}
        ))

    nat_eip = aws.ec2.Eip("nat-eip", domain="vpc")
    nat_gw = aws.ec2.NatGateway("nat-gw", subnet_id=public_subnets[0].id, allocation_id=nat_eip.allocation_id)

    return vpc, public_subnets, private_subnets, igw, nat_gw
