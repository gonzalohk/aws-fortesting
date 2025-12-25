import time
from typing import Optional, Tuple

import boto3
import botocore
import pytest
import requests


STACK_NAME = "myadmin-stack-x"
EXPECTED_TEXT = "Hello from the app"


def _get_stack_output(cfn_client, stack_name: str, key: str) -> str:
    resp = cfn_client.describe_stacks(StackName=stack_name)
    stacks = resp.get("Stacks", [])
    if not stacks:
        raise AssertionError(f"Stack not found: {stack_name}")

    outputs = stacks[0].get("Outputs", [])
    for o in outputs:
        if o.get("OutputKey") == key:
            return o.get("OutputValue")

    available = [o.get("OutputKey") for o in outputs]
    raise AssertionError(
        f"Output key '{key}' not found in stack outputs. Available outputs: {available}"
    )


def _find_target_group_arn_from_stack(cfn_client, stack_name: str) -> Optional[str]:
    """
    Attempts to discover the Target Group ARN via CloudFormation resource listing.
    This avoids hardcoding ARNs and makes the test portable.
    """
    paginator = cfn_client.get_paginator("list_stack_resources")
    for page in paginator.paginate(StackName=stack_name):
        for r in page.get("StackResourceSummaries", []):
            if r.get("ResourceType") == "AWS::ElasticLoadBalancingV2::TargetGroup":
                # For TargetGroup, PhysicalResourceId is typically the TargetGroup ARN.
                return r.get("PhysicalResourceId")
    return None

