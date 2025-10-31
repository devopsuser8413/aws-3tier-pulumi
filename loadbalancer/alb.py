import pulumi_aws as aws

def create_alb(vpc_id, public_subnets, alb_sg, private_instances):
    alb = aws.lb.LoadBalancer("alb", load_balancer_type="application", subnets=[s.id for s in public_subnets], security_groups=[alb_sg.id])
    tg = aws.lb.TargetGroup("app-tg", vpc_id=vpc_id, port=5000, protocol="HTTP", health_check=aws.lb.TargetGroupHealthCheckArgs(path="/"))

    for i, inst in enumerate(private_instances):
        aws.lb.TargetGroupAttachment(f"attach-{i+1}", target_group_arn=tg.arn, target_id=inst.id, port=5000)

    listener = aws.lb.Listener(
        "http-listener",
        load_balancer_arn=alb.arn,
        port=80,
        protocol="HTTP",
        default_actions=[aws.lb.ListenerDefaultActionArgs(type="forward", target_group_arn=tg.arn)]
    )

    return alb, tg, listener
