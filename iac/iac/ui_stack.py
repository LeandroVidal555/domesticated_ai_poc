import aws_cdk as cdk

from aws_cdk import(
    aws_s3 as s3
)

class UIStack(cdk.Stack):

    def __init__(self, scope: cdk.App, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cg = config["global"]
        cs = config["ui"]

        #####################################################
        ##### TAGS ##########################################
        #####################################################

        cdk.Tags.of(self).add("Owner", cg["tags"]["owner"])
        cdk.Tags.of(self).add("Project", cg["tags"]["project"])
        cdk.Tags.of(self).add("Environment", cg["tags"]["env"])
        cdk.Tags.of(self).add("PrimaryContact", cg["tags"]["contact"])


        #####################################################
        ##### S3 STATIC WEBSITE #############################
        #####################################################
        
        site_bucket = s3.Bucket(self, "SiteBucket",
            bucket_name = f"{cg['common_prefix']}-{cg['env']}-ui",
            website_index_document = "index.html",
            website_error_document = "error.html",
            public_read_access = True,
            block_public_access = s3.BlockPublicAccess(
                block_public_acls = False,
                block_public_policy = False,
                ignore_public_acls = False,
                restrict_public_buckets = False
            ),
            removal_policy = cdk.RemovalPolicy.DESTROY,
            auto_delete_objects = True, # delete object when deleting the bucket from the stack
        )