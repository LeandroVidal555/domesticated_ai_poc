{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Description": "Secrets Manager",
            "Effect": "Allow",
            "Action": "secretsmanager:GetSecretValue",
            "Resource": [
                "arn:aws:secretsmanager:${REGION}:${AWS_ACCOUNT_ID}:secret:${COMMON_PREFIX}-${ENV}-pgres-creds-*"
            ]
        },
        {
            "Description": "RDS Postgres allow",
            "Effect": "Allow",
            "Action": [
                "rds:*"
            ],
            "Resource": [
                "arn:aws:rds:${REGION}:${AWS_ACCOUNT_ID}:db:${COMMON_PREFIX}-${ENV}-pgres"
            ]
        },
        {
            "Description": "RDS Postgres deny",
            "Effect": "Deny",
            "Action": [
                "rds:DeleteDBInstance",
                "rds:DeleteDBCluster",
                "rds:DeleteDBSnapshot",
                "rds:DeleteDBClusterSnapshot",
                "rds:ModifyDBInstance",
                "rds:ModifyDBCluster",
                "rds:ModifyDBSubnetGroup",
                "rds:ModifyDBParameterGroup",
                "rds:StopDBInstance",
                "rds:StartDBInstance",
                "rds:RebootDBInstance",
                "rds:CreateDBSnapshot",
                "rds:CreateDBClusterSnapshot",
                "rds:RestoreDBInstanceFromDBSnapshot",
                "rds:RestoreDBClusterFromSnapshot",
                "rds:DownloadDBLogFilePortion",
                "rds:DescribeDBLogFiles",
                "rds:CreateDBInstance",
                "rds:CreateDBCluster",
                "rds:CreateDBInstanceReadReplica"
            ],
            "Resource": [
                "arn:aws:rds:${REGION}:${AWS_ACCOUNT_ID}:db:${COMMON_PREFIX}-${ENV}-pgres"
            ]
        },
        {
            "Description": "PGres DB connection",
            "Effect": "Allow",
            "Action": [
                "rds-db:connect"
            ],
            "Resource": [
                "arn:aws:rds-db:${REGION}:${AWS_ACCOUNT_ID}:dbuser:${PGRES_ID}/epwery"
            ]
        }
    ]
}
