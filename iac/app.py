#!/usr/bin/env python3
import yaml

import aws_cdk as cdk

from iac.net_stack import NetworkingStack
from iac.sec_stack import SecurityStack
from iac.com_stack import ComputeStack
from iac.db_stack  import DatabaseStack
from iac.acc_stack import AccessStack

# load config parameters from config file
with open("../config.yml", 'r') as file:
    config = yaml.safe_load(file)

account       = config['global']['account']
region        = config['global']['region']
common_prefix = config['global']['common_prefix']
env           = config['global']['env']

app = cdk.App()
NetworkingStack(app, f"{common_prefix}-{env}-networking-stack", config=config, env=cdk.Environment(account=account, region=region))
SecurityStack  (app, f"{common_prefix}-{env}-security-stack",   config=config, env=cdk.Environment(account=account, region=region))
ComputeStack   (app, f"{common_prefix}-{env}-compute-stack",    config=config, env=cdk.Environment(account=account, region=region))
DatabaseStack  (app, f"{common_prefix}-{env}-database-stack",   config=config, env=cdk.Environment(account=account, region=region))
AccessStack    (app, f"{common_prefix}-{env}-access-stack",     config=config, env=cdk.Environment(account=account, region=region))

app.synth()
