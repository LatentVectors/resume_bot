# LangSmith Components & Architecture

This document provides a compact and comprehensive guide for an LLM to the core architectural components of LangSmith, including the Control/Data Planes, Components, and the Agent Server.

## High-Level Architecture

LangSmith's architecture is fundamentally split into two parts to ensure security and operational separation. Your application's code and data are always handled in the Data Plane, while orchestration and monitoring are managed by the Control Plane.

### Control Plane

The Control Plane is the central LangSmith service managed by LangChain, accessible at `smith.langchain.com`.

- **Function**: It provides the web UI for managing deployments, datasets, and tests. It handles user authentication and orchestrates deployments to the Data Plane.
- **Data Access**: The Control Plane **does not** have access to your application's secrets, model inputs/outputs, or any other sensitive data. It only stores the metadata necessary for orchestration, along with the logs and traces you explicitly send to it.

### Data Plane

The Data Plane is the secure environment where your application code, models, and data reside.

- **Function**: It executes your agent's code, processes data, and interacts with models. It communicates with the Control Plane to receive deployment instructions and to send back traces and logs for monitoring.
- **Environment**: The Data Plane can be the LangChain-managed cloud infrastructure (used by LangGraph Deploy) or your own self-hosted environment (e.g., a private VPC).

## LangSmith Components

Components are the versioned, reusable building blocks of a LangSmith application.

- **Definition**: A Component is a `Runnable` or a `LangGraph` graph that is packaged for deployment. It is defined in a `pyproject.toml` file, which specifies its entry point and dependencies.
- **Versioning**: Each Component is versioned by a unique hash, ensuring that deployments are reproducible.
- **Lifecycle**:
  1.  **Define**: Configure the component in `pyproject.toml` under the `[tool.langsmith]` section.
  2.  **Build**: Use the `langsmith component build` command to package the component.
  3.  **Push**: Use `langsmith component push` to upload the versioned component to the Control Plane's registry. The Control Plane can then instruct a Data Plane to deploy it.

## Agent Server

The Agent Server is the runtime that executes Components in the Data Plane. It exposes a Component as a standardized REST API, simplifying interaction and integration.

- **Function**: It powers `langgraph deploy` and can be run locally for development or deployed in your own infrastructure. It provides a standard interface to invoke and manage agent runs.
- **Local Development vs. Production**:
  - `langgraph dev`: Starts a local development server using your `langgraph.json` file. It automatically reloads on code changes, making it ideal for iteration.
  - `langgraph serve`: Starts a production-ready server (using Gunicorn) for self-hosting.

### Standard API Endpoints

The Agent Server exposes the following core endpoints:

- `POST /runs`: Invoke the agent for a single, stateless run.
- `POST /threads`: Create a new conversational thread.
- `GET /threads/{thread_id}`: Retrieve the state of a thread.
- `POST /threads/{thread_id}/updates`: Update the state of a thread.
- `POST /threads/{thread_id}/run`: Invoke the agent within the context of an existing thread.

## How It All Connects

1.  You **define** a `Component` in your code and `pyproject.toml`.
2.  You **push** a version of this Component to the LangSmith Control Plane.
3.  From the Control Plane UI, you instruct a **Data Plane** to deploy that specific component version.
4.  The Data Plane spins up an **Agent Server** to host and execute your Component.
5.  Your client application interacts with the Agent Server's API to run the agent.
6.  The Agent Server sends traces and logs back to the **Control Plane** for monitoring.

## Mandatory Actions (MUST DO)

- **Develop Locally**: Always use `langgraph dev` to test your agent thoroughly before pushing a new component version or deploying.
- **Isolate Sensitive Data**: Ensure that models, data sources, and secrets reside only in your Data Plane.
- **Use Correct Serve Command**: Use `langgraph dev` for local development and `langgraph serve` for self-hosted production environments.
- **Version Components**: Use the `langsmith component push` workflow to create immutable, versioned components for reliable deployments.

## Prohibited Actions (AVOID)

- **Do not send secrets to the Control Plane**: Never include API keys or sensitive data in metadata sent to `smith.langchain.com`.
- **Avoid Bypassing the Agent Server API**: For deployed agents, always use the provided REST API. Do not attempt to interact with the underlying graph directly.

## Resources

- Components: https://docs.langchain.com/langsmith/components
- Agent Server: https://docs.langchain.com/langsmith/agent-server
- Data Plane: https://docs.langchain.com/langsmith/data-plane
- Control Plane: https://docs.langchain.com/langsmith/control-plane
