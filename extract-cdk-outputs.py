#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import sys


outputs_file = sys.argv[1]
with open(outputs_file) as fp:
    outputs_json = json.load(fp)

    amplify_app_id = outputs_json["image-reader-amplify-stack"]["ImageReaderAMPLIFYAPPID"]
    print(
f'''
1. To kick off frontend deployment, please run `aws amplify start-job --app-id {amplify_app_id} --branch-name main --job-type RELEASE` or visit https://console.aws.amazon.com/amplify/home -> All Apps -> ImageReader -> Run build.

2. After the deployment finishes (see https://console.aws.amazon.com/amplify/home -> All Apps -> ImageReader), visit {outputs_json["image-reader-amplify-stack"]["ImageReaderAMPLIFYAPPURL"]} and fill in the following values:
   S3 Bucket Name: {outputs_json["image-reader-s3-stack"]["ImageReaderS3BUCKETNAME"]}
   File Endpoint: {outputs_json["image-reader-main-stack"]["ImageReaderFILEAPIENDPOINT"]}
   Conversion Endpoint: {outputs_json["image-reader-main-stack"]["ImageReaderCONVERSIONAPIENDPOINT"]}
'''
    )
