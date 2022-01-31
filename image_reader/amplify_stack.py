# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import pathlib

from aws_cdk.core import CfnOutput, Construct, Stack
from aws_cdk.aws_amplify import App, CodeCommitSourceCodeProvider
from aws_cdk.aws_codecommit import CfnRepository, Repository
from aws_cdk.aws_s3_assets import Asset


TAG_NAME = 'app'
BRANCH_NAME = 'main'


class AmplifyStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        app_name = self.node.try_get_context('app-name')

        client_code_asset = Asset(
            scope=self,
            id=f'{app_name}-ASSET-CLIENT-CODE',
            path=str(pathlib.PurePath(__file__).parent.parent / 'client.zip')
        )

        code = CfnRepository.CodeProperty(
            s3=CfnRepository.S3Property(
                bucket=client_code_asset.s3_bucket_name,
                key=client_code_asset.s3_object_key,
            )
        )

        repository = CfnRepository(
            scope=self,
            id=f'{app_name}-CODECOMMIT-AMPLIFY-REPO-CFN',
            repository_name='amplify-image-reader',
            code=code,  # need to use the L1 construct CfnRepository instead of the L2 Repository to have this line
        )

        # Create an Amplify app with CodeCommit repo as the source code provider.
        # When code is checked in to that repo, amplify build is automatically triggered
        amplify_app = App(
            scope=self,
            id=f'{app_name}-AMPLIFY-APP',
            app_name=app_name,
            source_code_provider=CodeCommitSourceCodeProvider(
                repository=Repository.from_repository_arn(
                    scope=self,
                    id=f'{app_name}-CODECOMMIT-AMPLIFY-REPO',
                    repository_arn=repository.attr_arn,
                )
            )
        )

        branch = amplify_app.add_branch(
            id=BRANCH_NAME,
            auto_build=True,  # this does NOT trigger a build right after deployment
        )

        branch.add_environment('STAGE', 'prod')

        CfnOutput(
            scope=self,
            id=f'{app_name}-AMPLIFY-APP-ID',
            value=amplify_app.app_id,
        )

        CfnOutput(
            scope=self,
            id=f'{app_name}-AMPLIFY-APP-URL',
            value=f'https://{BRANCH_NAME}.{amplify_app.default_domain}',
        )

        # tag all resources with app_name
        self.tags.set_tag(TAG_NAME, app_name, apply_to_launched_instances=True)
