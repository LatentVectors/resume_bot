### Core Concepts

- **Assistant**: A specific configuration of a deployed graph. Assistants manage configurations like prompts, models, and tools separately from the graph's logic. Multiple assistants can use the same graph but have different configurations for specialized tasks.
- **Thread**: A sequence of operations that maintains state. To run a graph and persist its state, you must first create a thread.
- **Run**: An invocation of an assistant, executed on a thread. Each run can have its own input and configuration.

### Guidelines for Interaction

#### Must Do

- Always create a thread before running a graph to persist state.
- Use assistants to manage and version configurations.
- When updating an assistant, provide the _entire_ configuration, as updates create new versions from scratch.
- Manage different versions of an assistant by creating new versions with updated configurations.

#### Must Avoid

- Do not alter a graph's core logic for configuration changes. Use an assistant instead.
- Deleting an assistant will delete all of its versions.

### API and Configuration

#### LangGraph SDK Client

To interact with a deployment, first instantiate a client:

```python
from langgraph_sdk import get_client

client = get_client(url=<DEPLOYMENT_URL>)
```

#### Assistants

Assistants are instances of a graph with a specific configuration.

- **Create an Assistant**:

  ```python
  assistant = await client.assistants.create(
      graph_id="your_graph_id",
      config={"configurable": {"model_name": "gpt-4"}},
      name="My Assistant"
  )
  ```

- **Get an Assistant**:

  ```python
  assistant_details = await client.assistants.get(assistant["assistant_id"])
  ```

- **List Assistants**:

  ```python
  assistants = await client.assistants.search(graph_id="your_graph_id")
  ```

- **Update an Assistant (Creates a New Version)**:
  You must pass the entire `config` when updating.

  ```python
  assistant_v2 = await client.assistants.update(
      assistant["assistant_id"],
      config={
          "configurable": {
              "model_name": "gpt-4",
              "system_prompt": "You are a helpful assistant.",
          }
      },
  )
  ```

- **Set Active Version**:
  Roll back to a previous version by specifying the version number.

  ```python
  await client.assistants.set_latest(assistant['assistant_id'], 1)
  ```

- **Delete an Assistant**:
  This will delete all versions of the assistant.

  ```python
  await client.assistants.delete(assistant["assistant_id"])
  ```

#### Threads

Threads are required to run a graph and persist state.

- **Create a Thread**:

  - **Empty Thread**:

    ```python
    thread = await client.threads.create()
    ```

  - **Copy Thread**: Creates a new thread with an identical history to the original.

    ```python
    copied_thread = await client.threads.copy(<THREAD_ID>)
    ```

- **Inspect a Thread**:

  - **Get Thread**:

    ```python
    thread_details = await client.threads.get(<THREAD_ID>)
    ```

  - **Get Thread State**:
    View the current state of a thread. You can optionally pass a `checkpoint_id` to view a past state.

    ```python
    thread_state = await client.threads.get_state(<THREAD_ID>)
    ```

  - **Get Thread History**:
    Returns a list of every state the thread has experienced.

    ```python
    thread_history = await client.threads.get_history(<THREAD_ID>)
    ```

- **List Threads**:

  - **Search**:
    Filter by `status` ("idle", "busy", "interrupted", "error") or `metadata`.

    ```python
    idle_threads = await client.threads.search(status="idle", limit=10)
    ```

#### Runs

A run is an invocation of an assistant on a thread.

- **Stream a Run**:
  Execute a run and stream back updates. The `input` should be a list of messages.

  ```python
  thread = await client.threads.create()
  input = {"messages": [{"role": "user", "content": "Hello!"}]}
  async for event in client.runs.stream(
      thread["thread_id"],
      assistant["assistant_id"],
      input=input,
      stream_mode="updates",
  ):
      print(event.data)
  ```

### API Response Structures

#### Assistant Object

The object returned when creating or getting an assistant.

```json
{
  "assistant_id": "some-uuid-string",
  "graph_id": "your_graph_id",
  "name": "My Assistant",
  "config": {
    "configurable": {
      "model_name": "gpt-4"
    }
  },
  "metadata": {},
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

#### Thread Object

The object returned when creating or getting a thread.

```json
{
  "thread_id": "some-uuid-string",
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "metadata": {},
  "status": "idle",
  "values": {}
}
```

#### Run Stream Event

An event from the `client.runs.stream` generator. The `event` field indicates the type of data. Common events include `metadata` and `updates`.

```json
{
  "event": "updates",
  "data": {
    "agent": {
      "messages": [
        {
          "content": "Response message from the agent.",
          "type": "ai",
          "id": "run-some-uuid-string"
        }
      ]
    }
  },
  "run_id": "some-uuid-string"
}
```

### Resources

- https://docs.langchain.com/langsmith/assistants
- https://docs.langchain.com/langsmith/configuration-cloud
- https://docs.langchain.com/langsmith/use-threads
