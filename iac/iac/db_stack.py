import aws_cdk as cdk

from aws_cdk import(
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager
)


class DatabaseStack(cdk.Stack):

    def __init__(self, scope: cdk.App, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cg = config["global"]
        cs = config["database"]

        vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_name=f"{cg['common_prefix']}-{cg['env']}-vpc")

        sg_pgres = ec2.SecurityGroup.from_lookup_by_name(self, "SG_PGres", security_group_name=f"{cg['common_prefix']}-{cg['env']}-pgres-sg", vpc=vpc)
        #sg_postgres = ec2.SecurityGroup.from_lookup_by_id(self, "SG_PGres", security_group_id="sg-xxx")

        secret_pgres_creds = secretsmanager.Secret.from_secret_partial_arn(
            self, "Secret_PGres_Creds",
            secret_partial_arn=f"arn:aws:secretsmanager:{cg['region']}:{cg['account']}:secret:{cg['common_prefix']}-{cg['env']}-pgres-creds"
        )

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

        # Create RDS PostgreSQL instance
        rds.DatabaseInstance(
            self, "RDS_Pgres",
            instance_identifier = f"{cg['common_prefix']}-{cg['env']}-pgres",
            database_name = cs["database_name"],
            engine = rds.DatabaseInstanceEngine.postgres(
                version = rds.PostgresEngineVersion.VER_16_3),
            instance_type = ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE4_GRAVITON, ec2.InstanceSize.MICRO),
            vpc = vpc,
            vpc_subnets = ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            security_groups = [sg_pgres],
            multi_az = False,
            allocated_storage = 20,
            max_allocated_storage = 100,
            credentials = rds.Credentials.from_secret(secret_pgres_creds),
            publicly_accessible = False,
            iam_authentication = True
        )

# NOTE 1: you need to run the following to enable pgvector:
# CREATE EXTENSION vector;
# NOTE 2: you need to run the following to create the IAM authenticated dbuser:
# CREATE USER epwery;
# GRANT rds_iam TO epwery;


# TODO: come up with an automated method.


