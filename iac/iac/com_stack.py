import aws_cdk as cdk

from aws_cdk import(
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_ssm as ssm
)

import boto3

def get_ssm_parameters_by_path(path):
    """HS legacy: used to download all parameters for the lambda functions"""
    ssm_client = boto3.client('ssm')
    parameters = []
    next_token = None
    while True:
        if next_token:
            response = ssm_client.get_parameters_by_path(Path=path, Recursive=True, NextToken=next_token)
        else:
            response = ssm_client.get_parameters_by_path(Path=path, Recursive=True)
        parameters.extend(response['Parameters'])
        next_token = response.get('NextToken')
        if not next_token:
            break
    return parameters



def iac_output(value):
    """logging solution: write the output to an ssm parameter"""
    value = str(value)
    
    # ssm param value máx length is 4096 chars, truncate if exceeded
    if len(value) > 4096:
        value = value[:4085] + "[truncated]"

    ssm_client = boto3.client('ssm')
    ssm_client.put_parameter(Name="iac-output", Value=value, Type='String', Overwrite=True)



class ComputeStack(cdk.Stack):

    def __init__(self, scope: cdk.App, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cg = config["global"]
        cs = config["compute"]

        vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_name=f"{cg['common_prefix']}-{cg['env']}-vpc")
        role_ec2 = iam.Role.from_role_name(self, "Role_EC2", role_name=f"{cg['common_prefix']}-{cg['env']}-ec2-role")
        sg_ec2 = ec2.SecurityGroup.from_lookup_by_name(self, "SG_EC2", security_group_name=f"{cg['common_prefix']}-{cg['env']}-ec2-sg", vpc=vpc)


        #####################################################
        ##### TAGS ##########################################
        #####################################################

        cdk.Tags.of(self).add("Owner", cg["tags"]["owner"])
        cdk.Tags.of(self).add("Project", cg["tags"]["project"])
        cdk.Tags.of(self).add("Environment", cg["tags"]["env"])
        cdk.Tags.of(self).add("PrimaryContact", cg["tags"]["contact"])


        #####################################################
        ##### EC2 ###########################################
        #####################################################

        volume = ec2.BlockDevice(
            device_name="/dev/xvda",
            volume=ec2.BlockDeviceVolume.ebs(
                volume_size=27,
                volume_type=ec2.EbsDeviceVolumeType.GP3,
                delete_on_termination=False
            )
        )
        
        keypair_ec2 = ec2.KeyPair.from_key_pair_name(self, "KeyPair_EC2_Import", f"{cg['common_prefix']}-{cg['env']}-ec2-keypair")

        # Define the EC2 instance
        ec2_instance = ec2.Instance(
            self, "EC2_Instance",
            instance_name=f"{cg['common_prefix']}-{cg['env']}-ec2",
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ec2.MachineImage.latest_amazon_linux2023(),
            block_devices=[volume],
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_group=sg_ec2,
            key_pair=keypair_ec2,
            role=role_ec2,
        )

        ssm.StringParameter(
            self, "SSMParam_EC2_ID",
            parameter_name=f"/{cg['common_prefix']}-{cg['env']}/pipeline/ec2_instance_id",
            string_value=ec2_instance.instance_id
        )