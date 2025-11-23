# LangGraph Deploy: Agent-to-Agent (A2A) Communication Guide

This document provides concise guidelines for implementing and interacting with LangGraph Deploy agents using the Agent-to-Agent (A2A) Communication protocol.

## 1. Overview

LangGraph Deploy implements Google's A2A protocol, a standardized JSON-RPC interface for inter-agent communication. This enables predictable, stateful interactions between different language model agents.

## 2. Configuration Requirements

To enable the A2A endpoint, your LangGraph application must meet two conditions.

### 2.1. Dependency Version

Your project must use `langgraph-api` version `0.4.21` or newer.

### 2.2. Graph State Definition

The graph's state object **MUST** contain a `messages` key. The value must be a list of dictionaries. Each dictionary represents a message and should conform to the A2A message format.

```python
from typing import TypedDict, List, Dict, Any

class State(TypedDict):
    messages: List[Dict[str, Any]]
```

## 3. A2A API Interaction

A2A communication occurs through a dedicated endpoint, separate from the standard LangGraph Deploy thread endpoints.

### 3.1. Primary Endpoint

All A2A interactions are `POST` requests to a single endpoint:

- `POST /a2a/{assistant_id}`

The `{assistant_id}` is a unique identifier for your agent.

### 3.2. Agent Discovery (Agent Card)

An agent's capabilities and metadata can be discovered via its Agent Card.

- `GET /.well-known/agent-card.json?assistant_id={assistant_id}`

## 4. JSON-RPC Methods

The body of the `POST` request to the `/a2a/{assistant_id}` endpoint is a JSON-RPC 2.0 object specifying the method to invoke.

### Supported Methods

- `message/send`: Sends a message and waits for a complete, synchronous response.
- `message/stream`: Sends a message and receives a streamed response.
- `tasks/get`: Retrieves the status of an asynchronous task initiated by a previous call.

### Example Request (`message/send`)

```json
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "to": "assistant-id-123",
    "from": "user-id-456",
    "message": {
      "message_id": "msg-789",
      "content": {
        "parts": [{ "text": "Hello, agent!" }]
      }
    }
  }
}
```

## 5. Implementation Rules

### **MUST DO**

- Define a `messages: List[Dict[str, Any]]` key in your graph's `State` object. This is non-negotiable for A2A compatibility.
- Use `langgraph-api >= 0.4.21` to ensure the `/a2a` endpoint is available.
- Direct all A2A client interactions to the `POST /a2a/{assistant_id}` endpoint.

### **AVOID**

- Attempting A2A communication through the standard `/threads` endpoints. The A2A protocol uses its own dedicated endpoint and state management logic.
- Defining the state's `messages` key with a different type, such as `List[BaseMessage]`. For A2A, it must be `List[Dict[str, Any]]`.

## Resources

- https://docs.langchain.com/langsmith/server-a2a
