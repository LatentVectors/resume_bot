# LangGraph Deploy Guidelines

This document provides a compact and comprehensive guide for an LLM to interact with LangGraph Deploy. Follow these instructions to correctly configure, deploy, and manage LangGraph applications.

## Core Concepts

LangGraph Deploy is a feature within LangSmith for deploying LangGraph applications directly from a GitHub repository. It hosts the graph as a serverless API endpoint, enabling programmatic interaction and interactive testing in a managed cloud environment. Each deployment is linked to a specific Git branch.

## Deployment Workflow

Deployment is managed through the LangSmith UI.

1.  **Prerequisites**:
    - Application code must reside in a GitHub repository (public or private).
    - The application **MUST** run successfully locally via `langgraph dev`. Deployment will fail if local execution fails.
2.  **Initiate Deployment**: In the LangSmith UI, navigate to `Deployments` and select `+ New Deployment`.
3.  **Link Repository**: Connect your GitHub account and select the repository and branch containing the application. The GitHub user installing the LangChain app must be an owner of the organization.
4.  **Configure**:
    - **Deployment Name**: A unique identifier for the deployment.
    - **Config File**: The full path to the `langgraph.json` file from the repository root (e.g., `langgraph.json`).
    - **Git Branch**: The specific branch to deploy from.
    - **Automatic Updates**: Optionally, configure the deployment to automatically rebuild on a push to the linked branch.
    - **Deployment Type**: `Development` (minimal resources) or `Production` (highly available, up to 500 requests/second).
    - **Environment**: Set environment variables and secrets (e.g., `OPENAI_API_KEY`).
5.  **Deploy**: Submitting the configuration creates a "revision" and starts the build process.
6.  **Updates**: To deploy new code changes, create a new revision manually or have it triggered by a push to the linked branch.

## Interacting with a Deployed Graph

### Programmatic Interaction (SDK)

The primary method for interaction is via the `langgraph-sdk`. This allows you to stream outputs from the deployed graph.

```python
from langgraph_sdk import get_client

# Initialize the client
client = get_client(
    url="your-deployment-url",
    api_key="your-langsmith-api-key"
)

# Stream from the assistant
async for chunk in client.runs.stream(
    None,  # Use None for a threadless run
    "agent",  # Assistant name from langgraph.json
    input={"messages": [{"role": "human", "content": "What is LangGraph?"}]},
    stream_mode="updates",
):
    print(chunk)
```

### Interactive Testing (Studio)

Use the "Studio" button in the deployment details view within LangSmith. Studio provides a web UI to visualize, debug, and interact with your graph's structure and state. Deployments can be configured to be "Shareable through Studio," providing a direct URL for other LangSmith users.

## Key Configuration

### `langgraph.json`

This file is the entrypoint for your deployed application. It defines the assistants, tools, and other configurations for the LangGraph API. The path to this file must be specified correctly during deployment.

### Environment Variables & Secrets

- **Environment Variables**: Use for non-sensitive configuration.
- **Secrets**: **MUST** be used for sensitive data like API keys. Secrets are encrypted and securely stored.

## Mandatory Actions (MUST DO)

- **Verify Locally**: Before deploying, always confirm your application runs successfully with `langgraph dev`.
- **Use Secrets for Keys**: Store all credentials, API keys, and other sensitive information as secrets in the deployment configuration.
- **Specify Full Path**: Provide the complete path to the `langgraph.json` file from the repository root.
- **Monitor Logs**: Check build and server logs in the deployment view's `Revisions` panel to diagnose failures.
- **Check Monitoring Tab**: Use the `Monitoring` tab to view deployment metrics like latency and error rates.

## Prohibited Actions (AVOID)

- **Do not store secrets in code**: Never hardcode API keys or other secrets in your repository. Use the secrets manager in the deployment configuration.
- **Avoid using "Interrupt revision"**: This feature has undefined behavior and should only be used as a last resort if a deployment is unresponsive.

## API Reference: `langgraph-sdk`

### `get_client(url: str, api_key: str)`

Establishes a connection to the deployed LangGraph API.

- `url`: The API URL for your deployment, found in the deployment details view.
- `api_key`: A valid LangSmith API key for the workspace.

### `client.runs.stream(thread_id, assistant_id, input, stream_mode)`

Invokes the graph and streams back events.

- `thread_id`: A string identifying the thread, or `None` for a single, threadless run.
- `assistant_id`: The name of the assistant to invoke, as defined in `langgraph.json`.
- `input`: A dictionary containing the input for the graph.
- `stream_mode`: The streaming format. `"updates"` is recommended for receiving state updates.

## Resources

- Quickstart Guide: https://docs.langchain.com/langsmith/deployment-quickstart
- Cloud Deployment Guide: https://docs.langchain.com/langsmith/deploy-to-cloud
