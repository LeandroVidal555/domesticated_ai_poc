import aws_cdk as cdk

from aws_cdk import(
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as cf_origins,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    aws_elasticloadbalancingv2_targets as elbv2_targets,
    aws_ssm as ssm,
    aws_secretsmanager as secretsmanager
)


class AccessStack(cdk.Stack):

    def __init__(self, scope: cdk.App, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cg = config["global"]
        cs = config["access"]

        vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_name=f"{cg['common_prefix']}-{cg['env']}-vpc")

        sg_alb_ws = ec2.SecurityGroup.from_lookup_by_name(self, "SG_ALB_WS", security_group_name=f"{cg['common_prefix']}-{cg['env']}-alb-ws-sg", vpc=vpc)

        ec2_instance_id = ssm.StringParameter.from_string_parameter_name(
            self, "SSMParam_EC2_ID",
            string_parameter_name=f"/{cg['common_prefix']}-{cg['env']}/pipeline/ec2_instance_id"
        ).string_value

        #pgres_ip = ssm.StringParameter.from_string_parameter_name(
        #    self, "SSMParam_PGRES_IP",
        #    string_parameter_name=f"/{cg['common_prefix']}-{cg['env']}/pipeline/pgres_ip"
        #).string_value

        #####################################################
        ##### TAGS ##########################################
        #####################################################

        cdk.Tags.of(self).add("Owner", cg["tags"]["owner"])
        cdk.Tags.of(self).add("Project", cg["tags"]["project"])
        cdk.Tags.of(self).add("Environment", cg["tags"]["env"])
        cdk.Tags.of(self).add("PrimaryContact", cg["tags"]["contact"])


        """
        #####################################################
        ##### LOAD BALANCING - RDS NLB ######################
        #####################################################
        # NOTE: TEMPORARY. Only for development practices in staging acc.

        # Create an NLB
        nlb = elbv2.NetworkLoadBalancer(
            self, "NLB_PGres",
            load_balancer_name=f"{cg['common_prefix']}-{cg['env']}-pgres-nlb",
            vpc=vpc,
            internet_facing=True,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)
        )

        # Define a target group for port 5432
        target_group = elbv2.NetworkTargetGroup(
            self, "TG_PGres",
            target_group_name = f"{cg['common_prefix']}-{cg['env']}-pgres-nlb-tg",
            port=cs['pgres_port'],
            vpc=vpc,
            target_type = elbv2.TargetType.IP,
            protocol=elbv2.Protocol.TCP
        )

        target_group.add_target(
            elbv2_targets.IpTarget(
                ip_address=pgres_ip,
                port=5432
            )
        )  

        # Add a listener to the NLB
        nlb.add_listener("Listener_NLB_PGres", port=cs['pgres_port'], default_target_groups=[target_group])
        """


        #####################################################
        ##### LOAD BALANCING - EC2 ALB ######################
        #####################################################

        secret_cf_key = secretsmanager.Secret(
            self, "Secret_CF_Header_Key",
            secret_name=f"{cg['common_prefix']}-{cg['env']}-cf-header-key",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                exclude_punctuation=True,
                exclude_uppercase=True
            )
        ).secret_value.unsafe_unwrap()

        # Create the ALB
        alb_ws = elbv2.ApplicationLoadBalancer(
            self, "ALB_WebServer",
            load_balancer_name=f"{cg['common_prefix']}-{cg['env']}-webserver-alb",
            vpc=vpc,
            internet_facing=True,
            security_group=sg_alb_ws
        )
        
        tg_alb_ws = elbv2_targets.InstanceIdTarget(
            instance_id=ec2_instance_id,
            port=8080
        )

        # Add a listener for HTTP
        listener = alb_ws.add_listener(
            "Listener_ALB_WebServer",
            port=8080,
            open=True,
            default_action=elbv2.ListenerAction.fixed_response(
                status_code=400,
                content_type="text/plain",
                message_body="Bad request or wrong header key"
            )
        )

        # Add the default action to forward to the target group
        listener.add_targets(
            "TG_ALB_WebServer",
            target_group_name=f"{cg['common_prefix']}-{cg['env']}-alb-ws-tg",
            port=8080,
            targets=[tg_alb_ws],
            conditions=[
                elbv2.ListenerCondition.http_header(
                    name="x-cloudfront-secret-key",
                    values=[secret_cf_key]
                ),
                elbv2.ListenerCondition.path_patterns(
                    values=["/api/*"]
                )
            ],
            priority=1,
            health_check=elbv2.HealthCheck(
                path="/",
                port="8080",
                protocol=elbv2.Protocol.HTTP,
                healthy_threshold_count=2,
                interval=cdk.Duration.seconds(15)
            )
        )
        
        
        #####################################################
        ##### CLOUDFRONT - EC2 Webservice ###################
        #####################################################
    
        # CloudFront origin pointing to the EC2 instance
        origin = cf_origins.HttpOrigin(
            domain_name=alb_ws.load_balancer_dns_name,
            http_port=8080,
            protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY,
            custom_headers={"x-cloudfront-secret-key": secret_cf_key}
        )

        # CloudFront distribution
        cloudfront.Distribution(
            self, "CF_WS_Distribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origin,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER,
                response_headers_policy=cloudfront.ResponseHeadersPolicy.CORS_ALLOW_ALL_ORIGINS_WITH_PREFLIGHT_AND_SECURITY_HEADERS,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.HTTPS_ONLY
            )
        )