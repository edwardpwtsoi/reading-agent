# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Purpose

Shows how to use the AWS SDK for Python (Boto3) with the Amazon Bedrock Runtime client
to run inferences using Anthropic Claude 3 models.
"""

import json
import logging

import boto3
from botocore.exceptions import ClientError

from reading_agent.backends.base import BackendBase

logger = logging.getLogger(__name__)


# snippet-start:[python.example_code.bedrock-runtime.Claude3Wrapper.class]
class Claude3Backend(BackendBase):
    """Encapsulates Claude 3 model invocations using the Amazon Bedrock Runtime client."""

    def __init__(self, model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"):
        """
        :param client: A low-level client representing Amazon Bedrock Runtime.
                       Describes the API operations for running inference using Bedrock models.
                       Default: None
        """
        # Initialize the Amazon Bedrock runtime client
        self.client = boto3.client(
            service_name="bedrock-runtime", region_name="us-east-1"
        )
        self.model_id = model_id

    def query_model(self, prompt):
        result = self.invoke_claude_3_with_text(prompt)
        input_tokens = result["usage"]["input_tokens"]
        output_tokens = result["usage"]["output_tokens"]
        return input_tokens + output_tokens, result["content"][0]["text"]

    def _process_response(self, response):
        # Process and logger.info the response
        result = json.loads(response.get("body").read())
        input_tokens = result["usage"]["input_tokens"]
        output_tokens = result["usage"]["output_tokens"]
        output_list = result.get("content", [])

        logger.info("Invocation details:")
        logger.info(f"- The input length is {input_tokens} tokens.")
        logger.info(f"- The output length is {output_tokens} tokens.")

        logger.info(f"- The model returned {len(output_list)} response(s):")
        for output in output_list:
            logger.info(output["text"])

        return result

    def invoke_claude_3_with_text(self, prompt):
        """
        Invokes Anthropic Claude 3 Sonnet to run an inference using the input
        provided in the request body.

        :param prompt: The prompt that you want Claude 3 to complete.
        :return: Inference response from the model.
        """


        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(
                    {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 1024,
                        "messages": [
                            {
                                "role": "user",
                                "content": [{"type": "text", "text": prompt}],
                            }
                        ],
                    }
                ),
            )
            result = self._process_response(response)
            return result

        except ClientError as err:
            logger.error(
                f"Couldn't invoke {self.model_id}. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

    def invoke_claude_3_multimodal(self, prompt, base64_image_data):
        """
        Invokes Anthropic Claude 3 Sonnet to run a multimodal inference using the input
        provided in the request body.

        :param prompt:            The prompt that you want Claude 3 to use.
        :param base64_image_data: The base64-encoded image that you want to add to the request.
        :return: Inference response from the model.
        """

        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image_data,
                            },
                        },
                    ],
                }
            ],
        }

        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
            )
            result = self._process_response(response)
            return result
        except ClientError as err:
            logger.error(
                "Couldn't invoke Claude 3 Sonnet. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
