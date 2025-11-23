# LangGraph Generative UI Documentation

This document provides guidelines for an LLM on how to create, configure, and interact with LangGraph's Generative UI features.

## 1. Overview

LangGraph Generative UI allows agents to generate and interact with rich, dynamic user interfaces (UIs) in addition to text-based responses. The agent backend, built with LangGraph, sends UI component specifications to a React-based frontend, which then dynamically renders and manages these components.

## 2. Core Concepts

- **Backend (LangGraph)**: The agent logic resides here. It decides when to send, update, or remove UI components based on the conversational state.
- **Frontend (React)**: A client-side application that receives UI specifications from the backend and renders them using a dedicated React library.
- **`langgraph.json`**: A configuration file that maps UI component names to their source code files, enabling the framework to bundle and serve them for remote fetching.

## 3. Backend Implementation (Python)

### 3.1. State Definition

The agent's state must include a `ui` field to hold UI messages. Use the `ui_message_reducer` to correctly manage this part of the state.

```python
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langgraph.graph.ui import AnyUIMessage, ui_message_reducer

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    ui: Annotated[Sequence[AnyUIMessage], ui_message_reducer]
```

### 3.2. Sending UI Components

To send a UI component to the frontend, use the `push_ui_message` function within a graph node.

- **`push_ui_message(name: str, props: dict, message: BaseMessage = None, id: str = None, merge: bool = False)`**:
  - `name`: The unique identifier for the UI component.
  - `props`: A dictionary of properties to pass to the React component.
  - `message` (optional): The `AIMessage` to associate this UI component with.
  - `id` (optional): A specific ID for the UI message. If provided, subsequent calls with the same `id` can update this specific component instance.
  - `merge` (optional): If `True`, the new `props` will be merged with existing props for the given `id`. Defaults to `False`, which replaces the props.

### 3.3. Updating and Removing UI Components

- **To update a component**: Call `push_ui_message` again with the `id` of the message to update.
- **To remove a component**: Use the `delete_ui_message(id: str)` function with the ID of the UI message to remove.

### 3.4. Streaming UI Messages

When streaming the agent's state to the client, you must use `render_ui_messages` to process the `ui` field from the state into a format the frontend can render.

- **`render_ui_messages(chunk: dict)`**:
  - `chunk`: A state dictionary chunk received from the graph stream (e.g., `{'ui': [...]}`).
  - **Returns**: A list of serializable UI message dictionaries to be sent to the client.

**Example Usage:**

```python
# In your server endpoint
async for chunk in graph.astream(input, config=config):
    if "ui" in chunk:
        yield {"event": "data", "data": json.dumps(render_ui_messages(chunk))}
```

### 3.5. Configuration (`langgraph.json`)

This file links the component `name` used in `push_ui_message` to the file containing the component's code for remote fetching.

```json
{
  "ui": {
    "agent": "./src/agent/ui.tsx"
  }
}
```

## 4. Frontend Implementation (React)

### 4.1. Connecting to the Backend

Use the `useStream` hook to establish a connection with the LangGraph agent and receive state updates.

- **`useStream({ apiUrl, assistantId, onCustomEvent })`**:
  - Returns: `{ thread, values }` where `thread` contains messages and `values` contains other state variables, including `ui`.

### 4.2. Rendering UI Components

Use the `LoadExternalComponent` to dynamically render UI components sent from the backend.

- **`<LoadExternalComponent />` Props**:
  - `stream`: The `thread` object returned by `useStream`.
  - `message`: The specific UI message object from `values.ui`.
  - `fallback` (optional): A React element to display while the component is loading.
  - `components` (optional): A map of pre-loaded components on the client to bypass remote fetching.
  - `meta` (optional): Additional context to pass to the UI component.

### 4.3. Component Interactivity

Inside a dynamically loaded UI component, use the `useStreamContext` hook to access the thread state and submit data back to the agent.

- **`useStreamContext()`**:
  - **Returns**: `{ thread, submit, meta }`.
    - `submit(messages: ..., files: ...)`: A function to send data back to the LangGraph agent.

### 4.4. Bypassing Remote Fetching with Local Components

For performance optimization and to use components already in your application bundle, you can provide a map of pre-loaded components to the `LoadExternalComponent`. When a UI message is received, `LoadExternalComponent` first checks this map. If a component with a matching `name` is found, it renders it directly, skipping the network request.

**How to Use:**

1.  **Define your local components** in your React application as you normally would.
2.  **Create a map** where keys are the component names (the same string used in `push_ui_message` on the backend) and values are the component definitions.
3.  **Pass this map** to the `components` prop of `LoadExternalComponent`.

**Example:**

```tsx
"use client";
import { useStream } from "@langchain/langgraph-sdk/react";
import { LoadExternalComponent } from "@langchain/langgraph-sdk/react-ui";

// 1. Define a local component
const LocalWeatherComponent = ({ city }: { city: string }) => {
  return <div style={{ color: "blue" }}>Local weather for {city}</div>;
};

// 2. Create the components map
const localComponents = {
  // The key "weather" must match the `name` sent from the backend
  weather: LocalWeatherComponent,
};

export default function Page() {
  const { thread, values } = useStream(/* ... */);

  return (
    <div>
      {/* ... message mapping logic ... */}
      {values.ui
        ?.filter((ui) => ui.metadata?.message_id === message.id)
        .map((ui) => (
          <LoadExternalComponent
            key={ui.id}
            stream={thread}
            message={ui}
            // 3. Pass the map to the component
            components={localComponents}
            fallback={<div>Loading component...</div>}
          />
        ))}
    </div>
  );
}
```

In this example, if the backend sends a UI message with `name: "weather"`, the `LocalWeatherComponent` will be rendered immediately without fetching from the URL specified in `langgraph.json`. If a component name is not found in the `localComponents` map, `LoadExternalComponent` will proceed with remote fetching as the default behavior.

## 5. Guidelines

### MUST DO

- **Define UI State**: Always include `ui: Annotated[Sequence[AnyUIMessage], ui_message_reducer]` in your `AgentState`.
- **Use `render_ui_messages`**: When streaming, always process state chunks with this function to correctly format UI data for the client.
- **Register Components**: Register all remotely-fetched UI components in `langgraph.json`.
- **Use Local Components for Performance**: For common or simple components, provide them in the `components` map on the frontend to bypass network requests.
- **Associate UI with Messages**: When possible, use the `message` argument in `push_ui_message` to link a UI component to an AI message.
- **Use `LoadExternalComponent`**: This is the required method for rendering server-defined UI on the client.
- **Use `useStreamContext` for Interactivity**: For actions within a UI component that need to communicate back to the agent, use the `submit` function.

### MUST AVOID

- **Do Not Hardcode UI in Text**: Do not send HTML or Markdown for UI elements in regular message content.
- **Do Not Manage UI State Manually**: Rely entirely on the data received through the `useStream` hook.
- **Do Not Forget Fallbacks**: Provide a `fallback` prop to `LoadExternalComponent` to handle loading states gracefully.

# Resources

https://docs.langchain.com/langsmith/generative-ui-react
