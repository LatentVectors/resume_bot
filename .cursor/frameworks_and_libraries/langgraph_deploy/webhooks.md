# LangGraph Deploy Interaction Guide

This document provides guidelines for interacting with a deployed LangGraph service. The focus is on client-side interaction, state management through threads, and event-driven communication using webhooks.

## 1. Core Concepts

- **Deployment**: A LangGraph graph deployed as a persistent service.
- **Client**: Interaction is primarily through the `langgraph_sdk`.
- **Thread**: Represents a single conversation or session. State is persisted per `thread_id`.
- **Webhook**: An optional HTTP endpoint called by the service upon completion of a run to notify external systems.

## 2. Client Interaction

All interactions with a deployed graph are performed via a client instance.

### 2.1. Initialization

Instantiate the client by connecting to the deployment's URL.

```python
from langgraph_sdk import get_client

# The URL of your deployed LangGraph service
deployment_url = "YOUR_DEPLOYMENT_URL"

client = get_client(url=deployment_url)
```

### 2.2. Managing Threads

Stateful interactions require a thread. Create a new thread for each distinct conversation.

```python
# Create a new thread
thread = await client.threads.create()
thread_id = thread["thread_id"]
```

### 2.3. Executing Runs

Invoke the graph with input data for a specific thread. The primary method for this is `runs.stream`.

```python
# Define input for the graph
graph_input = {
    "messages": [{"role": "user", "content": "Hello!"}]
}

# Stream the run for a given thread and assistant
async for chunk in client.runs.stream(
    thread_id=thread_id,
    assistant_id="your_assistant_id", # Or graph_id
    input=graph_input,
    stream_mode="events"
):
    # Process stream chunks
    pass
```

## 3. Using Webhooks

Webhooks enable event-driven actions by triggering an external service when a run completes.

### 3.1. Attaching a Webhook

Specify the `webhook` parameter in an API call. LangSmith will send a POST request to this URL upon run completion.

```python
# The endpoint in your service that will receive the webhook
webhook_url = "https://my-server.app/my-webhook-endpoint"

async for chunk in client.runs.stream(
    thread_id=thread_id,
    assistant_id="your_assistant_id",
    input=graph_input,
    stream_mode="events",
    webhook=webhook_url
):
    pass
```

### 3.2. Securing Webhooks

To ensure requests originate from LangSmith, embed a secret token in the webhook URL as a query parameter. Your endpoint must validate this token.

```python
# Example of a secured webhook URL
secure_webhook_url = "https://my-server.app/my-webhook-endpoint?token=YOUR_SECRET_TOKEN"
```

### 3.3. Webhook Payload

The payload sent to the webhook URL is a `Run` object, containing the run's input, configuration, and other metadata.

### 3.4. Disabling Webhooks (Server-Side)

In self-hosted deployments, webhooks can be disabled globally for security. This is configured in the `langgraph.json` file on the server.

```json
{
  "http": {
    "disable_webhooks": true
  }
}
```

## 4. Guidelines

### MUST

- Use the `langgraph_sdk.get_client` to connect to a deployed graph.
- Create and use `thread_id` to manage state for conversations.
- To receive a callback on run completion, provide a URL in the `webhook` parameter of your API call.
- Validate incoming webhook requests if you use a security token.

### AVOID

- Assuming the `langgraph_sdk` can create webhook endpoints. You must implement and host your own service to listen for webhook POST requests.
- Passing sensitive information in webhook URLs without a proper validation mechanism.

## Resources

- [https://docs.langchain.com/langsmith/use-webhooks](https://docs.langchain.com/langsmith/use-webhooks)
