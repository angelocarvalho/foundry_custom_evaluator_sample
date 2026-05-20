from pathlib import Path
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import EvaluatorCategory, EvaluatorDefinitionType

# Azure AI Project endpoint
# Example: https://<account_name>.services.ai.azure.com/api/projects/<project_name>
FOUNDRY_PROJECT_ENDPOINT = "https://<account_name>.services.ai.azure.com/api/projects/<project_name>"

def load_prompt_text() -> str:
    """Load evaluator instructions from evaluator_prompt.txt located beside this script."""
    prompt_path = Path(__file__).with_name("evaluator_prompt.txt")
    return prompt_path.read_text(encoding="utf-8")

# Create the project client
project_client = AIProjectClient(
    endpoint=FOUNDRY_PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
)

# Register a prompt-based evaluator version in the Foundry project.
prompt_evaluator = project_client.beta.evaluators.create_version(
    name="communication_skills_evaluator",
    evaluator_version={
        "name": "communication_skills_evaluator",
        "categories": [EvaluatorCategory.QUALITY],
        "display_name": "Communication Skills Evaluator",
        "description": "Evaluates how effectively the agent responds to a negative or frustrated customer statement",
        "definition": {
            "type": EvaluatorDefinitionType.PROMPT,
            "prompt_text": load_prompt_text(),
            "init_parameters": {
                "type": "object",
                "properties": {
                    "deployment_name": {"type": "string"},
                    "threshold": {"type": "number"},
                },
                "required": ["deployment_name", "threshold"],
            },
            "data_schema": {
                "type": "object",
                "properties": {
                    "customer_statement": {"type": "string"},
                    "agent_response": {"type": "string"},
                },
                "required": ["customer_statement", "agent_response"],
            },
            "metrics": {
                "custom_prompt": {
                    "type": "ordinal",
                    "desirable_direction": "increase",
                    "min_value": 1,
                    "max_value": 5,
                }
            },
        },
    },
)