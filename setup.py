# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="image_reader",
    version="0.0.1",

    description="A CDK Python app",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="author",

    package_dir={"": "image_reader"},
    packages=setuptools.find_packages(where="image_reader"),

    install_requires=[
        "aws-cdk.core==1.122.0",
        "aws-cdk.aws_s3_assets==1.122.0",
        "aws-cdk.aws-amplify==1.122.0",
        "aws-cdk.aws-apigateway==1.122.0",
        "aws-cdk.aws-apigatewayv2==1.122.0",
        "aws-cdk.aws-dynamodb==1.122.0",
        "aws-cdk.aws-iam==1.122.0",
        "aws-cdk.aws-lambda==1.122.0",
        "aws-cdk.aws-s3==1.122.0",
        "aws-cdk.aws-sns==1.122.0",
        "aws-cdk.aws-sns-subscriptions==1.122.0",
        "aws-cdk.aws-stepfunctions==1.122.0",
        "aws-cdk.aws-stepfunctions-tasks==1.122.0",
        "boto3==1.17.90",
        "aws-cdk.aws-codecommit==1.122.0",
        "img2pdf==0.4.3"
    ],

    python_requires=">=3.6",

    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",

        "License :: OSI Approved :: MIT No Attribution License (MIT-0)",

        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",

        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",

        "Typing :: Typed",
    ],
)
