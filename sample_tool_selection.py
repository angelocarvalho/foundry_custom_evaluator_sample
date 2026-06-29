# pylint: disable=line-too-long,useless-suppression
# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------
#
# NOTE: This is a variation of the original sample:
# https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/ai/azure-ai-projects/samples/evaluations/agentic_evaluators/sample_tool_selection.py
#
# Additional test cases have been added to illustrate:
#   - A single-tool call scenario (weather query only)
#   - A wrong tool selection scenario (failure case) where the agent calls
#     the incorrect tool for the given user query
# ------------------------------------

"""
DESCRIPTION:
    Given an AIProjectClient, this sample demonstrates how to use the synchronous
    `openai.evals.*` methods to create, get and list evaluation and and eval runs
    for Tool Selection evaluator using inline dataset content.

USAGE:
    python sample_tool_selection.py

    Before running the sample:

    pip install "azure-ai-projects>=2.0.0" python-dotenv

    Set these environment variables with your own values:
    1) FOUNDRY_PROJECT_ENDPOINT - Required. The Azure AI Project endpoint, as found in the overview page of your
       Microsoft Foundry project. It has the form: https://<account_name>.services.ai.azure.com/api/projects/<project_name>.
    2) FOUNDRY_MODEL_NAME - Required. The name of the model deployment to use for evaluation.
"""

import os
import time
from pprint import pprint

from dotenv import load_dotenv

from openai.types.evals.create_eval_jsonl_run_data_source_param import (
    CreateEvalJSONLRunDataSourceParam,
    SourceFileContent,
    SourceFileContentContent,
)
from openai.types.eval_create_params import DataSourceConfigCustom
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import TestingCriterionAzureAIEvaluator

load_dotenv()


def main() -> None:
    endpoint = os.environ[
        "FOUNDRY_PROJECT_ENDPOINT"
    ]  # Sample : https://<account_name>.services.ai.azure.com/api/projects/<project_name>
    model_deployment_name = os.environ.get("FOUNDRY_MODEL_NAME", "")  # Sample : gpt-4o-mini

    # Use DefaultAzureCredential to authenticate with Azure services (supports managed identity,
    # environment variables, and interactive login depending on the execution environment).
    # AIProjectClient is the entry point to the Azure AI Foundry project.
    # get_openai_client() returns an OpenAI-compatible client scoped to this project,
    # which exposes the evals API used throughout this sample.
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=endpoint, credential=credential) as project_client,
        project_client.get_openai_client() as client,
    ):
        print("Creating an OpenAI client from the AI Project client")

        # Define the schema that each evaluation data item must conform to.
        # This tells the service which fields to expect in every test case:
        #   - query: the user message (string or conversation array)
        #   - response: the agent's response (string or conversation array)
        #   - tool_calls: explicit tool call records, if any (optional)
        #   - tool_definitions: the tools available to the agent during the conversation
        # 'include_sample_schema' makes the service surface an example item in the UI.
        data_source_config = DataSourceConfigCustom(
            type="custom",
            item_schema={
                "type": "object",
                "properties": {
                    "query": {"anyOf": [{"type": "string"}, {"type": "array", "items": {"type": "object"}}]},
                    "response": {"anyOf": [{"type": "string"}, {"type": "array", "items": {"type": "object"}}]},
                    "tool_calls": {"anyOf": [{"type": "object"}, {"type": "array", "items": {"type": "object"}}]},
                    "tool_definitions": {"anyOf": [{"type": "object"}, {"type": "array", "items": {"type": "object"}}]},
                },
                "required": ["query", "response", "tool_definitions"],
            },
            include_sample_schema=True,
        )

        # Configure the built-in 'tool_selection' evaluator as the testing criterion.
        # This evaluator uses a model-as-judge approach: it inspects the agent's tool calls
        # against the available tool definitions and the original user query, then scores
        # whether the agent selected the right tools in the right order.
        # data_mapping links each evaluator input to the corresponding field in the data item
        # using template syntax ({{item.<field>}}).
        testing_criteria = [
            TestingCriterionAzureAIEvaluator(
                type="azure_ai_evaluator",
                name="tool_selection",
                evaluator_name="builtin.tool_selection",
                initialization_parameters={"model": f"{model_deployment_name}"},
                data_mapping={
                    "query": "{{item.query}}",
                    "response": "{{item.response}}",
                    "tool_calls": "{{item.tool_calls}}",
                    "tool_definitions": "{{item.tool_definitions}}",
                },
            )
        ]

        # Create the evaluation definition in the service. This registers the schema and
        # testing criteria but does not run anything yet — it is a reusable configuration
        # that can be executed multiple times with different datasets (eval runs).
        print("Creating Evaluation")
        eval_object = client.evals.create(
            name="Test Tool Selection Evaluator with inline data",
            data_source_config=data_source_config,
            testing_criteria=testing_criteria,  # type: ignore
        )
        print("Evaluation created")

        # Retrieve the evaluation object to confirm it was created successfully.
        print("Get Evaluation by Id")
        eval_object_response = client.evals.retrieve(eval_object.id)
        print("Eval Run Response:")
        pprint(eval_object_response)

        # --- Test case 1 (PASS): multi-tool sequence ---
        # The user asks for weather info to be emailed. The agent correctly chains
        # two tool calls: first fetch_weather to get the data, then send_email to
        # deliver it. This should receive a high tool_selection score.
        query = "Can you send me an email with weather information for Seattle?"
        response = [
            {
                "createdAt": "2025-03-26T17:27:35Z",
                "run_id": "run_zblZyGCNyx6aOYTadmaqM4QN",
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_call",
                        "tool_call_id": "call_CUdbkBfvVBla2YP3p24uhElJ",
                        "name": "fetch_weather",
                        "arguments": {"location": "Seattle"},
                    }
                ],
            },
            {
                "createdAt": "2025-03-26T17:27:37Z",
                "run_id": "run_zblZyGCNyx6aOYTadmaqM4QN",
                "tool_call_id": "call_CUdbkBfvVBla2YP3p24uhElJ",
                "role": "tool",
                "content": [{"type": "tool_result", "tool_result": {"weather": "Rainy, 14\u00b0C"}}],
            },
            {
                "createdAt": "2025-03-26T17:27:38Z",
                "run_id": "run_zblZyGCNyx6aOYTadmaqM4QN",
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_call",
                        "tool_call_id": "call_iq9RuPxqzykebvACgX8pqRW2",
                        "name": "send_email",
                        "arguments": {
                            "recipient": "your_email@example.com",
                            "subject": "Weather Information for Seattle",
                            "body": "The current weather in Seattle is rainy with a temperature of 14\u00b0C.",
                        },
                    }
                ],
            },
            {
                "createdAt": "2025-03-26T17:27:41Z",
                "run_id": "run_zblZyGCNyx6aOYTadmaqM4QN",
                "tool_call_id": "call_iq9RuPxqzykebvACgX8pqRW2",
                "role": "tool",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_result": {"message": "Email successfully sent to your_email@example.com."},
                    }
                ],
            },
            {
                "createdAt": "2025-03-26T17:27:42Z",
                "run_id": "run_zblZyGCNyx6aOYTadmaqM4QN",
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "I have successfully sent you an email with the weather information for Seattle. The current weather is rainy with a temperature of 14\u00b0C.",
                    }
                ],
            },
        ]

        # Tool definitions describe every tool the agent had access to during the conversation.
        # The evaluator uses these definitions to judge whether the agent's tool choices
        # were appropriate for each user query.
        tool_definitions = [
            {
                "name": "fetch_weather",
                "description": "Fetches the weather information for the specified location.",
                "parameters": {
                    "type": "object",
                    "properties": {"location": {"type": "string", "description": "The location to fetch weather for."}},
                },
            },
            {
                "name": "send_email",
                "description": "Sends an email with the specified subject and body to the recipient.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "recipient": {"type": "string", "description": "Email address of the recipient."},
                        "subject": {"type": "string", "description": "Subject of the email."},
                        "body": {"type": "string", "description": "Body content of the email."},
                    },
                },
            },
        ]

        # --- Test case 3 (FAIL): wrong tool selected ---
        # The user only asks for the current weather. The correct tool is fetch_weather,
        # but the agent mistakenly calls send_email instead — skipping the actual weather
        # lookup entirely. This should receive a low tool_selection score, demonstrating
        # how the evaluator catches incorrect tool choices.
        query3 = "What is the weather like in Chicago?"
        response3 = [
            {
                "createdAt": "2025-03-26T17:29:00Z",
                "run_id": "run_wrong_tool",
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_call",
                        "tool_call_id": "call_wrong_tool",
                        "name": "send_email",
                        "arguments": {
                            "recipient": "user@example.com",
                            "subject": "Weather in Chicago",
                            "body": "I will look up the weather in Chicago for you.",
                        },
                    }
                ],
            },
            {
                "createdAt": "2025-03-26T17:29:02Z",
                "run_id": "run_wrong_tool",
                "tool_call_id": "call_wrong_tool",
                "role": "tool",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_result": {"message": "Email successfully sent to user@example.com."},
                    }
                ],
            },
            {
                "createdAt": "2025-03-26T17:29:03Z",
                "run_id": "run_wrong_tool",
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "I have sent you an email about the weather in Chicago.",
                    }
                ],
            },
        ]

        # --- Test case 2 (PASS): single tool call ---
        # The user asks only for the weather. The agent correctly calls fetch_weather
        # once and summarises the result in plain text — no email required.
        # This should receive a high tool_selection score.
        query2 = "How is the weather in New York City?"
        response2 = [
            {
                "createdAt": "2025-03-26T17:28:00Z",
                "run_id": "run_abc123",
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_call",
                        "tool_call_id": "call_abc123",
                        "name": "fetch_weather",
                        "arguments": {"location": "New York City"},
                    }
                ],
            },
            {
                "createdAt": "2025-03-26T17:28:02Z",
                "run_id": "run_abc123",
                "tool_call_id": "call_abc123",
                "role": "tool",
                "content": [{"type": "tool_result", "tool_result": {"weather": "Sunny, 22\u00b0C"}}],
            },
            {
                "createdAt": "2025-03-26T17:28:03Z",
                "run_id": "run_abc123",
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "The current weather in New York City is sunny with a temperature of 22\u00b0C.",
                    }
                ],
            },
        ]

        # Create an eval run by submitting all three test cases as inline JSONL content.
        # Each SourceFileContentContent item is one row the evaluator will score independently.
        # Passing tool_calls=None means the evaluator derives tool call information from
        # the response conversation turns rather than a separate explicit list.
        print("Creating Eval Run with Inline Data")
        eval_run_object = client.evals.runs.create(
            eval_id=eval_object.id,
            name="inline_data_run",
            metadata={"team": "eval-exp", "scenario": "inline-data-v1"},
            data_source=CreateEvalJSONLRunDataSourceParam(
                type="jsonl",
                source=SourceFileContent(
                    type="file_content",
                    content=[
                        SourceFileContentContent(
                            item={
                                "query": query,
                                "response": response,
                                "tool_calls": None,
                                "tool_definitions": tool_definitions,
                            }
                        ),
                        SourceFileContentContent(
                            item={
                                "query": query2,
                                "response": response2,
                                "tool_calls": None,
                                "tool_definitions": tool_definitions,
                            }
                        ),
                        SourceFileContentContent(
                            item={
                                "query": query3,
                                "response": response3,
                                "tool_calls": None,
                                "tool_definitions": tool_definitions,
                            }
                        ),
                    ],
                ),
            ),
        )

        print("Eval Run created")
        pprint(eval_run_object)

        # Retrieve the eval run object immediately after creation to confirm it was accepted.
        print("Get Eval Run by Id")
        eval_run_response = client.evals.runs.retrieve(run_id=eval_run_object.id, eval_id=eval_object.id)
        print("Eval Run Response:")
        pprint(eval_run_response)

        print("\n\n----Eval Run Output Items----\n\n")

        # Poll the service every 5 seconds until the run reaches a terminal state.
        # Once complete, fetch and display the per-item output (one result per test case),
        # the overall status, and the URL of the full evaluation report in the portal.
        while True:
            run = client.evals.runs.retrieve(run_id=eval_run_response.id, eval_id=eval_object.id)
            if run.status in ("completed", "failed"):
                output_items = list(client.evals.runs.output_items.list(run_id=run.id, eval_id=eval_object.id))
                pprint(output_items)
                print(f"Eval Run Status: {run.status}")
                print(f"Eval Run Report URL: {run.report_url}")
                break
            time.sleep(5)
            print("Waiting for eval run to complete...")


if __name__ == "__main__":
    main()
