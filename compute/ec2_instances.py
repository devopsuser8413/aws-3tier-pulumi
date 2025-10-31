import pulumi_aws as aws

def create_instances(ami, instance_type, public_subnets, private_subnets, public_sg, app_sg, user_data_public, user_data_private):
    instances_public = []
    instances_private = []

    for i, subnet in enumerate(public_subnets):
        instances_public.append(aws.ec2.Instance(
            f"public-ec2-{i+1}",
            ami=ami,
            instance_type=instance_type,
            subnet_id=subnet.id,
            vpc_security_group_ids=[public_sg.id],
            associate_public_ip_address=True,
            user_data=user_data_public,
            tags={"Name": f"public-ec2-{i+1}"}
        ))

    for i, subnet in enumerate(private_subnets):
        instances_private.append(aws.ec2.Instance(
            f"app-ec2-{i+1}",
            ami=ami,
            instance_type=instance_type,
            subnet_id=subnet.id,
            vpc_security_group_ids=[app_sg.id],
            associate_public_ip_address=False,
            user_data=user_data_private,
            tags={"Name": f"app-ec2-{i+1}"}
        ))

    return instances_public, instances_private
