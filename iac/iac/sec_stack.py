import aws_cdk as cdk

from aws_cdk import(
    aws_ec2 as ec2,
    aws_iam as iam,
)

import json

def attach_policy_doc(scope, file, role):
    """Add a policy to a role, providing a json file name"""

    with open(f"iac_backend/policy_docs/{file}.json", 'r') as policy_file:
        data = policy_file.read()
        policy_dict = json.loads(data)

    # To CamelCase
    id_prefix = "".join([part.capitalize() for part in file.split('_')])

    role.attach_inline_policy(iam.Policy(scope, f"{id_prefix}Permissions",
        document = iam.PolicyDocument.from_json(policy_dict),
    ))


class SecurityStack(cdk.Stack):

    def __init__(self, scope: cdk.App, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cg = config["global"]
        cs = config["security"]

        vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_name=f"{cg['common_prefix']}-{cg['env']}-vpc")

        #####################################################
        ##### TAGS ##########################################
        #####################################################

        cdk.Tags.of(self).add("Owner", cg["tags"]["owner"])
        cdk.Tags.of(self).add("Project", cg["tags"]["project"])
        cdk.Tags.of(self).add("Environment", cg["tags"]["env"])
        cdk.Tags.of(self).add("PrimaryContact", cg["tags"]["contact"])
        

        #####################################################
        ##### RDS POSTGRES ##################################
        #####################################################

        # Create a security group for the RDS instance
        sg_postgres = ec2.SecurityGroup(
            self, "SG_PGres",
            security_group_name = f"{cg['common_prefix']}-{cg['env']}-pgres-sg",
            vpc = vpc,
            description = "Allow access from EC2 instance"
        )


        #####################################################
        ##### EC2 ###########################################
        #####################################################

        # Create an IAM Role for the EC2 instance
        role_ec2 = iam.Role(
            self, "Role_EC2",
            role_name = f"{cg['common_prefix']}-{cg['env']}-ec2-role",
            assumed_by = iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies = [
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore")
            ],
            description="Role for the EC2 instance"
        )
        attach_policy_doc(self, "role_ec2", role_ec2)

        # Create a security group for the ALB pointing to EC2 instance
        sg_alb_ec2 = ec2.SecurityGroup(
            self, "SG_ALB_WS",
            security_group_name = f"{cg['common_prefix']}-{cg['env']}-alb-ws-sg",
            vpc = vpc,
            description = "SG for ALB pointing to the WebServer in EC2 instance"
        )

        # Add rules to allow access from 8080 CloudFront origins
        sg_alb_ec2.add_ingress_rule(
            peer=ec2.Peer.prefix_list(cs['cf_prefix_list']),
            connection=ec2.Port.tcp(8080),
            description="Allow HTTPS traffic only from 8080 CloudFront origins"
        )

        # Create a security group for the EC2 instance
        sg_ec2 = ec2.SecurityGroup(
            self, "SG_EC2",
            security_group_name = f"{cg['common_prefix']}-{cg['env']}-ec2-sg",
            vpc = vpc,
            description = "SG for EC2 instance"
        )

        # Allow traffic from the ALB (introduced as its SG)
        sg_ec2.add_ingress_rule(
            peer=ec2.Peer.security_group_id(sg_alb_ec2.security_group_id),
            connection=ec2.Port.tcp(8080),
            description="Allow traffic from ALB (this is its SG id)"
        )

        # Add rules to allow access to RDS from the EC2 instance
        sg_postgres.add_ingress_rule(peer=sg_ec2, connection=ec2.Port.tcp(cs["pgres_port"]))
        # sg_postgres.add_ingress_rule(peer=nlb_ip1, connection=ec2.Port.tcp(cs["pgres_port"]))
        # sg_postgres.add_ingress_rule(peer=nlb_ip2, connection=ec2.Port.tcp(cs["pgres_port"]))
