# LangGraph Deploy LLM Interaction Guide

This document provides guidelines for an LLM to interact with, configure, and use LangGraph Deploy, with a focus on authentication and authorization.

## Core Concepts

- **Authentication (AuthN)**: Verifies the identity of a user or service for every incoming request. This is handled by a single `@auth.authenticate` handler.
- **Authorization (AuthZ)**: Determines what an authenticated user or service is permitted to do. This is handled by `@auth.on` handlers for specific resources and actions.

## Authentication

Authentication runs as middleware for every request. Your primary tool is the `langgraph_sdk.Auth` object.

### `langgraph.json` Configuration

To enable custom authentication, specify the path to your `Auth` object in `langgraph.json`.

```json
{
  "auth": {
    "path": "src/security/auth.py:auth"
  }
}
```

This tells LangGraph to use your defined authentication and authorization logic for the deployment.

### Authentication Handler: `@auth.authenticate`

This decorator registers a function to handle authentication. It runs on every request.

- **Purpose**: Validate credentials from the request and return structured user information.
- **Input**: The handler can accept various request components by name, including `authorization: str | None`, `headers: dict`, `cookies: dict`, `query: dict`, and `request: Request`. LangGraph performs dependency injection based on the function signature.
- **Output (Success)**: Must return a `MinimalUserDict`. This is a dictionary containing a required `identity` key (a unique string for the user) and any other custom fields.
- **Output (Failure)**: Must raise an `Auth.exceptions.HTTPException` or an `AssertionError`.

#### `MinimalUserDict` Structure

```python
from typing import TypedDict

class MinimalUserDict(TypedDict, total=False):
    """
    A dictionary representing the authenticated user.
    Must contain at least the 'identity' key.
    """
    identity: str
    # You can add other custom fields, e.g.:
    # permissions: list[str]
    # tenant_id: str
```

#### Example `@auth.authenticate` Handler

```python
from langgraph_sdk import Auth

auth = Auth()

@auth.authenticate
async def get_current_user(authorization: str | None) -> Auth.types.MinimalUserDict:
    """Validate token and return user info."""
    if not authorization:
        raise Auth.exceptions.HTTPException(status_code=401, detail="Missing Authorization header")

    scheme, _, token = authorization.partition(' ')
    if scheme.lower() != "bearer" or not token:
        raise Auth.exceptions.HTTPException(status_code=401, detail="Invalid token scheme")

    # In a real application, validate the token against an identity provider.
    # user_info = await my_identity_provider.validate(token)
    # if not user_info:
    #     raise Auth.exceptions.HTTPException(status_code=401, detail="Invalid token")
    # return user_info

    # Example using hard-coded tokens (for development only):
    VALID_TOKENS = {
        "user1-token": {"id": "user1", "permissions": ["read"]},
        "user2-token": {"id": "user2", "permissions": ["read", "write"]},
    }
    if token not in VALID_TOKENS:
        raise Auth.exceptions.HTTPException(status_code=401, detail="Invalid token")

    user_data = VALID_TOKENS[token]
    return {"identity": user_data["id"], "permissions": user_data.get("permissions", [])}
```

The returned user dictionary is accessible in authorization handlers via `ctx.user` and in your graph via `config["configurable"]["langgraph_auth_user"]`.

## Authorization

Authorization handlers run after successful authentication to control access to resources. LangGraph executes the most specific matching handler for a given resource and action.

- **Specificity Order**: `@auth.on.<resource>.<action>` > `@auth.on.<resource>` > `@auth.on`

### Authorization Handlers: `@auth.on`

The `@auth.on` decorator registers an authorization handler.

#### Handler Signature

An authorization handler receives two arguments:

- `ctx: Auth.types.AuthContext`: An object containing contextual information.
- `value: dict`: The resource being created or accessed.

#### `AuthContext` Structure

```python
import dataclasses

@dataclasses.dataclass
class AuthContext:
    """Context object passed to authorization handlers."""
    user: MinimalUserDict  # The authenticated user object.
    resource: str          # The resource being accessed (e.g., 'threads').
    action: str            # The action being performed (e.g., 'create').
```

#### Handler Return Value

- **`dict` (Metadata Filter)**:
  - On **create/update**: The key-value pairs in the dictionary are **added** to the resource's metadata.
  - On **read/search/delete**: The dictionary acts as a **filter**. Only resources whose metadata matches these key-value pairs will be returned or deleted.
- **`True` or `None`**: Unconditionally grants access.
- **`False`**: Denies access, raising a 403 Forbidden error.

#### Common Pattern: Single-Owner Resources

This pattern ensures that users can only access the resources they create.

```python
@auth.on
async def add_owner(ctx: Auth.types.AuthContext, value: dict) -> dict:
    """Make resources private to their creator."""
    owner_filter = {"owner": ctx.user.get("identity")}

    # On create/update actions, inject the owner into the resource's metadata.
    if ctx.action in ["create", "update"]:
        metadata = value.setdefault("metadata", {})
        metadata.update(owner_filter)

    # For all actions, return the filter to restrict access to the owner.
    return owner_filter
```

### Supported Resources and Actions

- **Resources**: `threads`, `assistants`, `crons`
- **Actions**: `create`, `read`, `update`, `delete`, `search`

Note: Run access is controlled by the parent `thread`'s handlers, except for the `create_run` action.

## OpenAPI Security Schema

To document your API's authentication requirements for clients, add an `openapi` field to your `auth` configuration in `langgraph.json`. This populates the OpenAPI specification but does not implement security logic.

```json
{
  "auth": {
    "path": "./auth.py:auth",
    "openapi": {
      "securitySchemes": {
        "BearerAuth": {
          "type": "http",
          "scheme": "bearer"
        }
      },
      "security": [{ "BearerAuth": [] }]
    }
  }
}
```

## Must-Do

- **Implement Custom Authentication**: For any deployment, implement an `@auth.authenticate` handler to validate credentials against a secure identity provider (e.g., Auth0, Supabase, Okta).
- **Implement Authorization**: Use `@auth.on` handlers to enforce resource-level permissions. Make conversations (`threads`) private by default.
- **Centralize User Management**: Use a dedicated authentication provider for user identities, credentials, and tokens.
- **Pass Tokens Securely**: Clients must include the authentication token in the `Authorization` header for every request.
- **Securely Store Secrets**: Use environment variables and secure secret stores. Do not hard-code tokens or secrets in your code.

## Avoid

- **Using Hard-Coded Tokens in Production**: A static dictionary of tokens is for development and testing only.
- **Storing Secrets in Graph State**: Do not pass secrets or sensitive user data through the graph state.
- **Disabling Studio Auth Carelessly**: When self-hosting, setting `disable_studio_auth: true` prevents developers from accessing the deployment via the Studio UI unless they also provide valid end-user credentials.
- **Leaving Self-Hosted Deployments Unsecured**: By default, self-hosted deployments have no authentication. You MUST implement your own security model.

---

## Resources

- [Authentication & access control](https://docs.langchain.com/langsmith/auth)
- [Add custom authentication](https://docs.langchain.com/langsmith/custom-auth)
- [Set up custom authentication](https://docs.langchain.com/langsmith/set-up-custom-auth)
- [Make conversations private](https://docs.langchain.com/langsmith/resource-auth)
- [Connect an authentication provider](https://docs.langchain.com/langsmith/add-auth-server)
- [Document API authentication in OpenAPI](https://docs.langchain.com/langsmith/openapi-security)
