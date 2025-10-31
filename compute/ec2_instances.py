import pulumi
import pulumi_aws as aws


def create_instances(
    ami_id,
    instance_type,
    public_subnets,
    private_subnets,
    public_sg,
    app_sg,
    user_data_public,
    user_data_private,
    key_name
):
    """
    Create EC2 instances for both public (bastion) and private (app) tiers.

    Args:
        ami_id (str): The AMI ID to use for EC2 instances.
        instance_type (str): EC2 instance type (e.g., t3.micro).
        public_subnets (list): List of Pulumi Subnet resources for public tier.
        private_subnets (list): List of Pulumi Subnet resources for private tier.
        public_sg (aws.ec2.SecurityGroup): Security group for public instances.
        app_sg (aws.ec2.SecurityGroup): Security group for private instances.
        user_data_public (str): User data script for public instances.
        user_data_private (str): User data script for private instances.
        key_name (str): Name of the SSH key pair.

    Returns:
        tuple: Lists of public and private EC2 instances.
    """

    public_instances = []
    private_instances = []

    # --------------------------
    # Public EC2 Instances (Bastion / Monitoring)
    # --------------------------
    for i, subnet in enumerate(public_subnets):
        instance = aws.ec2.Instance(
            f"public-ec2-{i+1}",
            ami=ami_id,
            instance_type=instance_type,
            subnet_id=subnet.id,
            vpc_security_group_ids=[public_sg.id],
            associate_public_ip_address=True,
            key_name=key_name,
            # ✅ Pass user data for setup
            user_data=user_data_public,
            tags={
                "Name": f"public-ec2-{i+1}",
                "Tier": "public",
                "ManagedBy": "Pulumi"
            }
        )
        public_instances.append(instance)

        pulumi.export(f"public_instance_{i+1}_id", instance.id)
        pulumi.export(f"public_instance_{i+1}_public_ip", instance.public_ip)

    # --------------------------
    # Private EC2 Instances (Application Tier)
    # --------------------------
    for i, subnet in enumerate(private_subnets):
        instance = aws.ec2.Instance(
            f"private-ec2-{i+1}",
            ami=ami_id,
            instance_type=instance_type,
            subnet_id=subnet.id,
            vpc_security_group_ids=[app_sg.id],
            associate_public_ip_address=False,
            key_name=key_name,
            # ✅ Attach user data for Flask app setup
            user_data=user_data_private,
            tags={
                "Name": f"private-ec2-{i+1}",
                "Tier": "private",
                "ManagedBy": "Pulumi"
            }
        )
        private_instances.append(instance)

        pulumi.export(f"private_instance_{i+1}_id", instance.id)
        pulumi.export(f"private_instance_{i+1}_private_ip", instance.private_ip)

    pulumi.export("total_public_instances", len(public_instances))
    pulumi.export("total_private_instances", len(private_instances))

    return public_instances, private_instances
