# LangGraph Deploy Integration Guide for LLMs

This document provides guidelines for interacting with LangGraph Deploy, primarily through the `@langchain/langgraph-sdk/react` library.

## Core Component: `useStream` Hook

The `useStream` React hook is the primary interface for integrating LangGraph into a React application. It manages streaming, state, and branching.

### Installation

```bash
npm install @langchain/langgraph-sdk @langchain/core
```

### Basic Usage

```javascript
import { useStream } from "@langchain/langgraph-sdk/react";

const thread = useStream({
  apiUrl: "http://localhost:2024",
  assistantId: "agent",
  messagesKey: "messages",
});
```

## API Reference

### `useStream` Configuration

| Argument           | Type                         | Description                                                                                                                                                |
| ------------------ | ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apiUrl`           | `string`                     | **Required.** The URL of the agent server.                                                                                                                 |
| `assistantId`      | `string`                     | **Required.** The ID of the assistant to connect to.                                                                                                       |
| `messagesKey`      | `string`                     | The key in the state object where messages are stored. Defaults to `"messages"`.                                                                           |
| `threadId`         | `string`                     | The ID of the conversation thread to load.                                                                                                                 |
| `onThreadId`       | `(threadId: string) => void` | Callback invoked when a new thread is created.                                                                                                             |
| `reconnectOnMount` | `boolean` \| `() => Storage` | If `true`, resumes a stream on component mount. Defaults to `false`. Can be a function that returns a storage object (`localStorage` or `sessionStorage`). |
| `initialValues`    | `T`                          | Cached thread data to display while history is loading.                                                                                                    |

### Returned Properties and Methods

| Property/Method         | Type                                                    | Description                                                           |
| ----------------------- | ------------------------------------------------------- | --------------------------------------------------------------------- |
| `messages`              | `Message[]`                                             | An array of message objects from the stream.                          |
| `isLoading`             | `boolean`                                               | `true` when a stream is active.                                       |
| `interrupt`             | `InterruptType`                                         | The last interrupt from the thread. `null` if no interrupt is active. |
| `submit()`              | `(values: UpdateType, options?: SubmitOptions) => void` | Submits data to the stream.                                           |
| `stop()`                | `() => void`                                            | Stops the active stream.                                              |
| `joinStream()`          | `(runId: string) => void`                               | Manually resumes a stream.                                            |
| `getMessagesMetadata()` | `(message: Message) => MessageMetadata`                 | Retrieves metadata for a message, used for branching.                 |
| `setBranch()`           | `(branch: string) => void`                              | Switches to a different conversation branch.                          |

### `submit()` Options

| Option             | Type             | Description                                                       |
| ------------------ | ---------------- | ----------------------------------------------------------------- |
| `checkpoint`       | `string`         | The checkpoint to start the run from, used for branching.         |
| `streamResumable`  | `boolean`        | If `true`, the stream can be resumed later.                       |
| `optimisticValues` | `(prev: T) => T` | A function to optimistically update the client state.             |
| `threadId`         | `string`         | The ID to use for the new thread, for optimistic thread creation. |

## Key Concepts and Guidelines

### MUST DO

- **Provide `apiUrl` and `assistantId`**: These are required to connect to the LangGraph deployment.
- **Manage Loading States**: Use the `isLoading` property to provide user feedback and prevent duplicate submissions.
- **Handle Interrupts**: Check the `interrupt` property to handle cases where the agent needs human input.
- **Persist `threadId`**: Store the `threadId` (e.g., in URL search params) to allow users to resume conversations.

### AVOID

- **Modifying `messages` directly**: The `useStream` hook manages the `messages` array. Use `submit` to send new messages.
- **Ignoring `isLoading`**: Submitting new data while `isLoading` is `true` can lead to unexpected behavior.

## Advanced Usage

### Branching

To create a new conversation branch (e.g., regenerate a response or edit a message):

1.  Use `getMessagesMetadata(message)` to get the `parent_checkpoint`.
2.  Call `submit()` with the `checkpoint` option set to the `parent_checkpoint`.

```javascript
// Regenerate an AI message
const meta = thread.getMessagesMetadata(message);
const parentCheckpoint = meta?.firstSeenState?.parent_checkpoint;
thread.submit(undefined, { checkpoint: parentCheckpoint });
```

### Optimistic Updates

Provide immediate feedback by updating the UI before the server responds.

```javascript
const newMessage = { type: "human", content: "Hello" };
stream.submit(
  { messages: [newMessage] },
  {
    optimisticValues(prev) {
      const prevMessages = prev.messages ?? [];
      return { ...prev, messages: [...prevMessages, newMessage] };
    },
  }
);
```

### TypeScript

For type safety, provide generic arguments to `useStream`.

```typescript
type State = { messages: Message[] };
type Update = { messages: Message[] | Message };
type Interrupt = string;

const thread = useStream<
  State,
  { UpdateType: Update; InterruptType: Interrupt }
>({
  // ...config
});
```

### Event Handling

Use callbacks in the `useStream` configuration to respond to stream lifecycle events.

| Callback          | Description                                           |
| ----------------- | ----------------------------------------------------- |
| `onCreated`       | Called when a new run is created.                     |
| `onError`         | Called when an error occurs.                          |
| `onFinish`        | Called when the stream finishes.                      |
| `onUpdateEvent`   | Called when a state update is received.               |
| `onCustomEvent`   | Called for custom events from the graph.              |
| `onMetadataEvent` | Called when metadata (run ID, thread ID) is received. |

## Custom Events

Custom events allow the server-side graph to stream arbitrary JSON data to the client, separate from the main state updates. This is useful for sending intermediate data, like tool outputs or other annotations, as they happen.

- **Server-Side**: Within a graph node (in Python), use the write_events function to yield data with a custom event name.
- **Client-Side**: On the client, the onCustomEvent callback provided to the useStream hook will be invoked. The callback receives the event name and the data payload, allowing the application to react to these custom server-sent events in real-time.

# References

https://docs.langchain.com/langsmith/use-stream-react
https://reference.langchain.com/javascript/modules/_langchain_langgraph-sdk.html
