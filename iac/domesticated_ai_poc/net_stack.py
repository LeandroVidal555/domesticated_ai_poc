import aws_cdk as cdk

from aws_cdk import(
    aws_ec2 as ec2
)


class NetworkingStack(cdk.Stack):

    def __init__(self, scope: cdk.App, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cg = config["global"]
        cs = config["networking"]

        #####################################################
        ##### TAGS ##########################################
        #####################################################

        cdk.Tags.of(self).add("Owner", cg["tags"]["owner"])
        cdk.Tags.of(self).add("Project", cg["tags"]["project"])
        cdk.Tags.of(self).add("Environment", cg["tags"]["env"])
        cdk.Tags.of(self).add("PrimaryContact", cg["tags"]["contact"])


        #####################################################
        ##### VPC ###########################################
        #####################################################

        ### VPC + Subnets (3 private, 3 isolated, 3 public)
        vpc = ec2.Vpc(
            self, "VPC_BACKEND",
            vpc_name = f"{cg['common_prefix']}-{cg['env']}-vpc",
            ip_addresses = ec2.IpAddresses.cidr(cs["vpc_cidr"]),
            max_azs = cs["az_count"],
            nat_gateways = 1,
            subnet_configuration = [
                ec2.SubnetConfiguration(
                    name = f"{cg['common_prefix']}-{cg['env']}-{cs['public_subnet_name']}",
                    subnet_type = ec2.SubnetType.PUBLIC,
                    cidr_mask = cs["public_subnet_prefix"]
                ),
                ec2.SubnetConfiguration(
                    name = f"{cg['common_prefix']}-{cg['env']}-{cs['private_subnet_name']}",
                    subnet_type = ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask = cs["private_subnet_prefix"]
                ),
                ec2.SubnetConfiguration(
                    name = f"{cg['common_prefix']}-{cg['env']}-{cs['isolated_subnet_name']}",
                    subnet_type = ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask = cs["isolated_subnet_prefix"]
                )
            ]
        )

        # Need to tag subnets post-creation for naming
        for i, subnet in enumerate(vpc.public_subnets, start=1):
            cdk.Tags.of(subnet).add("Name", f"{cg['common_prefix']}-{cg['env']}-{cs['public_subnet_name']}-{i}{subnet.availability_zone[-1]}")
        for i, subnet in enumerate(vpc.private_subnets, start=1):
            cdk.Tags.of(subnet).add("Name", f"{cg['common_prefix']}-{cg['env']}-{cs['private_subnet_name']}-{i}{subnet.availability_zone[-1]}")
        for i, subnet in enumerate(vpc.isolated_subnets, start=1):
            cdk.Tags.of(subnet).add("Name", f"{cg['common_prefix']}-{cg['env']}-{cs['isolated_subnet_name']}-{i}{subnet.availability_zone[-1]}")
