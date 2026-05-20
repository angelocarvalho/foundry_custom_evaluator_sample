# Foundry Custom Evaluator Sample

This folder contains a sample implementation for creating and running a custom prompt-based evaluator using Azure AI Projects (Foundry) and OpenAI. The evaluator is designed to assess the communication quality of an agent's response to negative or frustrated customer statements.

## Purpose
- Demonstrates how to register a prompt-based evaluator in Azure AI Foundry.
- Shows how to run the evaluator on sample data and retrieve evaluation results.
- Provides a reusable template for building your own custom evaluators.

## Folder Contents
- `create_prompt_based_evaluator.py`: Registers a prompt-based evaluator in your Foundry project using a prompt template.
- `evaluator_prompt.txt`: The prompt template used by the evaluator to score agent responses.
- `run_custom_evaluator.py`: Runs the registered evaluator on a set of sample customer/agent interactions and prints the evaluation report URL.
- `requirements.txt`: Python dependencies required to run the scripts.

## Prerequisites
- Python 3.8+
- An Azure subscription with access to Azure AI Projects (Foundry)
- An Azure AI Project endpoint and a deployed model (e.g., GPT-4, GPT-5)
- Azure CLI or environment variables configured for authentication

## Setup
1. Create and activate a Python virtual environment (recommended):
   ```sh
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Set your Azure credentials (if not already configured):
   - Use `az login` or set environment variables for service principal authentication.

## Usage
1. **Register the Evaluator**
   - Edit `create_prompt_based_evaluator.py` and set your `FOUNDRY_PROJECT_ENDPOINT`.
   - Run the script:
     ```sh
     python create_prompt_based_evaluator.py
     ```
2. **Run the Evaluator**
   - Edit `run_custom_evaluator.py` and set your `FOUNDRY_PROJECT_ENDPOINT` and `AZURE_AI_MODEL_DEPLOYMENT_NAME`.
   - Run the script:
     ```sh
     python run_custom_evaluator.py
     ```
   - The script will print a report URL with evaluation results.

## Notes
- The evaluator prompt (`evaluator_prompt.txt`) can be customized for different evaluation criteria.
- Sample data in `run_custom_evaluator.py` can be replaced with your own test cases.

## License
MIT License
