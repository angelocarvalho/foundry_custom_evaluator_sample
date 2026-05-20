import time
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from openai.types.eval_create_params import DataSourceConfigCustom
from openai.types.evals.create_eval_jsonl_run_data_source_param import (
    CreateEvalJSONLRunDataSourceParam,
    SourceFileContent,
    SourceFileContentContent,
)

# Azure AI Project endpoint
# Example: https://<account_name>.services.ai.azure.com/api/projects/<project_name>
FOUNDRY_PROJECT_ENDPOINT = "https://<account_name>.services.ai.azure.com/api/projects/<project_name>"

# Model deployment name (required for prompt-based evaluators)
# Example: gpt-5-mini
AZURE_AI_MODEL_DEPLOYMENT_NAME = "gpt-5"
POLL_INTERVAL_SECONDS = 5

def build_inline_items() -> list[SourceFileContentContent]:
    """Build inline dataset items used by the evaluator run."""
    return [
        # Good communication
        SourceFileContentContent(
            item={
                "customer_statement": "I’ve been waiting for a refund for over two weeks. This is unacceptable.",
                "agent_response": "I’m really sorry for the delay—that’s definitely not the experience we want for you. Let me check the status of your refund right now and make sure it gets resolved as quickly as possible. I’ll follow up with you shortly with an update.",
            }
        ),
        SourceFileContentContent(
            item={
                "customer_statement": "This product doesn’t work at all. I wasted my money.",
                "agent_response": "I completely understand how frustrating that must be, and I’m sorry you’re dealing with this. Let’s fix this together—could you share a bit more about the issue you’re seeing? I’ll help you troubleshoot or arrange a replacement if needed.",
            }
        ),
        SourceFileContentContent(
            item={
                "customer_statement": "I’ve contacted support three times and nobody has helped me.",
                "agent_response": "I’m really sorry you’ve had to go through that—thank you for your patience. I’ll take ownership of this and make sure we get it sorted out for you. Let me review your case now and provide a clear resolution or next steps.",
            }
        ),
        # Poor communication
        SourceFileContentContent(
            item={
                "customer_statement": "My order arrived damaged. What are you going to do about this?",
                "agent_response": "That’s not something we can control. You should contact the shipping company.",
            }
        ),
        SourceFileContentContent(
            item={
                "customer_statement": "I’ve been locked out of my account for days. This is ridiculous.",
                "agent_response": "You probably entered the wrong password too many times. Just wait and try again later.",
            }
        ),
        SourceFileContentContent(
            item={
                "customer_statement": "I canceled my subscription but I’m still being charged.",
                "agent_response": "Our system shows no issue on our side. Charges are correct.",
            }
        ),
        # Ambiguous / mixed
        SourceFileContentContent(
            item={
                "customer_statement": "This service is way too slow. I’m thinking of canceling.",
                "agent_response": "I understand your concern. We’re currently experiencing higher demand, which may affect speed.",
            }
        ),
        SourceFileContentContent(
            item={
                "customer_statement": "I’m really upset that my delivery is late again.",
                "agent_response": "Sorry about that. Your order should arrive soon.",
            }
        ),
        SourceFileContentContent(
            item={
                "customer_statement": "The instructions are confusing and I can’t set this up.",
                "agent_response": "You can find the setup steps in the manual or on our website.",
            }
        ),
    ]

def wait_for_run_completion(openai_client, eval_id: str, run_id: str):
    """Poll until the run reaches a terminal status."""
    while True:
        run = openai_client.evals.runs.retrieve(run_id=run_id, eval_id=eval_id)
        if run.status in ("completed", "failed"):
            return run
        time.sleep(POLL_INTERVAL_SECONDS)

# Create the project client
project_client = AIProjectClient(
    endpoint=FOUNDRY_PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
)

# Get the OpenAI client for evaluation API
client = project_client.get_openai_client()

# Define the data schema
data_source_config = DataSourceConfigCustom(
    type="custom",
    item_schema={
        "type": "object",
        "properties": {
            "response": {"type": "string"},
        },
        "required": ["response"],
    },
)

# Reference both custom evaluators in testing criteria
testing_criteria = [
    {
        "type": "azure_ai_evaluator",
        "name": "communication_skills_evaluator",
        "evaluator_name": "communication_skills_evaluator",
        "data_mapping": {
            "customer_statement": "{{item.customer_statement}}",
            "agent_response": "{{item.agent_response}}",
        },
        "initialization_parameters": {
            "deployment_name": AZURE_AI_MODEL_DEPLOYMENT_NAME,
            "threshold": 3,
        },
    },
]

# Create the evaluation
eval_object = client.evals.create(
    name="custom-eval-test",
    data_source_config=data_source_config,
    testing_criteria=testing_criteria,
)

# Run the evaluation with inline data
eval_run = client.evals.runs.create(
    eval_id=eval_object.id,
    name="custom-eval-run-01",
    data_source=CreateEvalJSONLRunDataSourceParam(
        type="jsonl",
        source=SourceFileContent(
            type="file_content",
            content=build_inline_items(),
        ),
    ),
)

# Wait for the run to finish before fetching outputs.
run = wait_for_run_completion(client, eval_object.id, eval_run.id)

# Get per-item results
output_items = list(
    client.evals.runs.output_items.list(run_id=run.id, eval_id=eval_object.id)
)

print(f"Report: {run.report_url}")