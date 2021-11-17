#!/usr/bin/env python3
import os
from aws_cdk import aws_iam as _iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_dynamodb as _ddb
from aws_cdk import aws_apigateway as _ag
from aws_cdk import core
from aws_cdk.pipelines import CodePipeline, CodePipelineSource, ShellStep



class VotingApiStack(core.Stack):
    def __init__(self, scope: core.Construct, construct_id: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Model all required resources
        ddb_table = _ddb.Table(
            self,
            id='{}-db'.format(construct_id),
            table_name='{}-db'.format(construct_id),
            partition_key=_ddb.Attribute(name='VOTE_ID',
                                         type=_ddb.AttributeType.STRING),
            # THIS IS NOT RECOMMENDED FOR PRODUCTION USE
            removal_policy=core.RemovalPolicy.DESTROY,
            read_capacity=5,
            write_capacity=5)

        # IAM Roles
        lambda_role = _iam.Role(
            self,
            id='{}-lambda-role'.format(construct_id),
            assumed_by=_iam.ServicePrincipal('lambda.amazonaws.com'))

        cw_policy_statement = _iam.PolicyStatement(effect=_iam.Effect.ALLOW)
        cw_policy_statement.add_actions("logs:CreateLogGroup")
        cw_policy_statement.add_actions("logs:CreateLogStream")
        cw_policy_statement.add_actions("logs:PutLogEvents")
        cw_policy_statement.add_actions("logs:DescribeLogStreams")
        cw_policy_statement.add_resources("*")
        lambda_role.add_to_policy(cw_policy_statement)

        # Add role for DynamoDB
        dynamodb_policy_statement = _iam.PolicyStatement(
            effect=_iam.Effect.ALLOW)
        dynamodb_policy_statement.add_actions("dynamodb:PutItem")
        dynamodb_policy_statement.add_actions("dynamodb:GetItem")
        dynamodb_policy_statement.add_actions("dynamodb:UpdateItem")
        dynamodb_policy_statement.add_actions("dynamodb:DeleteItem")
        dynamodb_policy_statement.add_actions("dynamodb:Scan")
        dynamodb_policy_statement.add_actions("dynamodb:Query")
        dynamodb_policy_statement.add_actions("dynamodb:ConditionCheckItem")
        dynamodb_policy_statement.add_resources(ddb_table.table_arn)
        lambda_role.add_to_policy(dynamodb_policy_statement)

        # AWS Lambda Functions
        fnLambda_vote = _lambda.Function(
            self,
            "{}-function-vote".format(construct_id),
            code=_lambda.AssetCode("../voting-api/vote_option"),
            handler="app.handler",
            timeout=core.Duration.seconds(60),
            role=lambda_role,
            runtime=_lambda.Runtime.PYTHON_3_8)
        fnLambda_vote.add_environment("TABLE_NAME", ddb_table.table_name)

        fnLambda_options = _lambda.Function(
            self,
            "{}-function-options".format(construct_id),
            code=_lambda.AssetCode("../voting-api/get_options"),
            handler="app.handler",
            timeout=core.Duration.seconds(60),
            role=lambda_role,
            runtime=_lambda.Runtime.PYTHON_3_8)
        fnLambda_options.add_environment("TABLE_NAME", ddb_table.table_name)

        api = _ag.RestApi(
            self,
            id="{}-api-gateway".format(construct_id),
            default_cors_preflight_options=_ag.CorsOptions(
            allow_methods=['ANY'],
            allow_origins=['*'],
            allow_headers=['Access-Control-Allow-Origin',
                'Access-Control-Allow-Headers', 'Content-Type']
            ))

        int_vote=_ag.LambdaIntegration(fnLambda_vote)
        int_options=_ag.LambdaIntegration(fnLambda_options)

        res_data=api.root.add_resource('vote')
        res_data.add_method('POST', int_vote)
        res_data.add_method('GET', int_options)

        core.CfnOutput(self, "{}-output-dynamodbTable".format(construct_id),
                       value=ddb_table.table_name, export_name="{}-ddbTable".format(construct_id))
        core.CfnOutput(self, "{}-output-apiEndpointURL".format(construct_id),
                       value=api.url, export_name="{}-apiEndpointURL".format(construct_id))

class VotingApiAppStage(core.Stage):
    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        VotingApiStack(self, "{}-api-pipeline".format(construct_id))

class VotingApiPipelineStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        pipeline =  CodePipeline(self, "{}-pipeline".format(construct_id),
                        pipeline_name="{}-pipeline".format(construct_id),
                        synth=ShellStep("Synth",
                            input=CodePipelineSource.git_hub("donnieprakoso/app-serverlessVoting-cdk", "main"),
                            commands=["npm install -g aws-cdk",
                                "python3 -m pip install -r requirements.txt",
                                "cdk synth"]))

        pipeline.add_stage(VotingApiAppStage(self, "test"))


AWS_ACCOUNT_ID=os.getenv("CDK_DEFAULT_ACCOUNT")
AWS_REGION=os.getenv("CDK_DEFAULT_REGION")
STACK_NAME='votingapp'
app=core.App()

# Defining staging environment
ENV_NAME="{}-staging".format(STACK_NAME)
votingapi_staging_stack=VotingApiStack(app, "{}-api".format(ENV_NAME))
core.Tags.of(votingapi_staging_stack).add('Name', STACK_NAME)

# Defining staging environment
ENV_NAME="{}-prod".format(STACK_NAME)
votingapi_prod_stack=VotingApiStack(app, "{}-api".format(ENV_NAME))
core.Tags.of(votingapi_prod_stack).add('Name', STACK_NAME)

votingapi_test_pipeline = VotingApiPipelineStack(app, "{}-pipeline".format(STACK_NAME))


app.synth()
