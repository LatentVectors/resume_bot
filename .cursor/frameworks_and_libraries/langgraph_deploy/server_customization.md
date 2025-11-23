# LangGraph Deploy Customization Guide

This document provides guidelines for customizing a LangGraph deployment by defining a custom Starlette/FastAPI application. All customizations require Python deployments with `langgraph-api>=0.0.26`.

## Core Concept: Custom Application

To customize the server, you provide a path to a Starlette or FastAPI application instance within the `langgraph.json` configuration file. This single mechanism enables the addition of custom routes, middleware, and lifespan event handling.

### Configuration (`langgraph.json`)

To enable customizations, point the `http.app` key to your application instance. The value must be a string in the format `"./path/to/file.py:app_instance_name"`.

```json
{
  "dependencies": ["."],
  "graphs": {
    "agent": "./src/agent/graph.py:graph"
  },
  "env": ".env",
  "http": {
    "app": "./src/agent/webapp.py:app"
  }
}
```

---

## Custom Routes

Add custom HTTP endpoints to your deployment to supplement or override default behavior.

### Must Do

- Define a FastAPI or Starlette application instance.
- Use standard decorators (`@app.get`, `@app.post`, etc.) to define routes.

### Example

```python
# ./src/agent/webapp.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/hello")
def read_root():
    return {"Hello": "World"}
```

### Avoid

- Accidentally shadowing default system endpoints. Custom routes are given priority and will override any default LangGraph endpoint with the same path, which can be a powerful tool for intentional redefinition.

---

## Custom Middleware

Intercept and process incoming requests and outgoing responses globally. This is useful for logging, header manipulation, or security policies.

### Must Do

- Use `starlette.middleware.base.BaseHTTPMiddleware`.
- The `dispatch` method must accept `request: Request` and `call_next` as arguments.
- **Crucially, you must `await call_next(request)`** to pass the request to the next handler and get the response.
- Add the middleware to your application instance using `app.add_middleware(...)`.

### Middleware Ordering

By default, custom middleware executes _before_ authentication logic. To run it _after_ authentication, which allows access to user context, configure `middleware_order`.

- **`middleware_order`**: Set to `"auth_first"` to ensure your middleware runs after the built-in authentication layer. (Requires API server v0.4.35+).

### Example

```python
# ./src/agent/webapp.py
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()

class CustomHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers['X-Custom-Header'] = 'value'
        return response

app.add_middleware(CustomHeaderMiddleware)
```

---

## Custom Lifespan Events

Manage resources during the server's startup and shutdown lifecycle. This is essential for initializing and closing database connections, models, or other external resources.

### Must Do

- Use an `asynccontextmanager` to define the lifespan logic.
- The function must accept the `app: FastAPI` instance as an argument.
- Store shared resources (like a database session factory) on the application state object, `app.state`.
- Code before the `yield` statement runs on **startup**.
- Code after the `yield` statement runs on **shutdown**.
- Register the context manager with the FastAPI application on initialization: `app = FastAPI(lifespan=lifespan)`.

### Example

```python
# ./src/agent/webapp.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
# Example: using sqlalchemy for a database connection
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize resources
    engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
    async_session = sessionmaker(engine, class_=AsyncSession)
    app.state.db_session = async_session
    yield
    # Shutdown: Clean up resources
    await engine.dispose()

app = FastAPI(lifespan=lifespan)
```

### Avoid

- Performing long-running blocking operations during startup, as this will delay server readiness.
- Forgetting to release all acquired resources (e.g., database connections, file handles) in the shutdown phase to prevent leaks.

---

## Resources

- **Custom Lifespan Events:** https://docs.langchain.com/langsmith/custom-lifespan
- **Custom Middleware:** https://docs.langchain.com/langsmith/custom-middleware
- **Custom Routes:** https://docs.langchain.com/langsmith/custom-routes
