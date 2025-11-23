## CLI Commands

The base command is `langgraph`.

### `langgraph dev`

Runs a lightweight local development server with hot-reloading. Does not require Docker.

**Usage:** `langgraph dev [OPTIONS]`

| Option                        | Default                       | Description                                                          |
| :---------------------------- | :---------------------------- | :------------------------------------------------------------------- |
| `-c`, `--config FILE`         | `langgraph.json`              | Path to the configuration file.                                      |
| `--host TEXT`                 | `127.0.0.1`                   | Host to bind the server to.                                          |
| `--port INTEGER`              | `2024`                        | Port to bind the server to.                                          |
| `--no-reload`                 | N/A                           | Disable automatic code reloading on changes.                         |
| `--n-jobs-per-worker INTEGER` | `10`                          | Number of jobs per worker.                                           |
| `--debug-port INTEGER`        | N/A                           | Port for a debugger to listen on.                                    |
| `--wait-for-client`           | `False`                       | Pause server startup until a debugger client connects.               |
| `--no-browser`                | N/A                           | Prevent automatically opening a web browser.                         |
| `--studio-url TEXT`           | `https://smith.langchain.com` | URL of the Studio instance to connect to.                            |
| `--allow-blocking`            | `False`                       | Do not raise errors for synchronous I/O blocking calls in your code. |
| `--tunnel`                    | `False`                       | Expose the local server via a public Cloudflare tunnel.              |
| `--help`                      | N/A                           | Display the help message for this command.                           |

### `langgraph build`

Builds a Docker image for the agent server.

**Usage:** `langgraph build [OPTIONS]`

| Option                   | Default          | Description                                                                    |
| :----------------------- | :--------------- | :----------------------------------------------------------------------------- |
| `--platform TEXT`        | N/A              | Target platform(s) for the Docker image (e.g., `linux/amd64,linux/arm64`).     |
| `-t`, `--tag TEXT`       | N/A              | **Required.** Tag for the Docker image (e.g., `my-agent:latest`).              |
| `--pull` / `--no-pull`   | `--pull`         | `--pull` to use the latest remote base image; `--no-pull` to use local images. |
| `-c`, `--config FILE`    | `langgraph.json` | Path to the configuration file.                                                |
| `--build-command TEXT`   | N/A              | _(JS Only)_ Build command to run from the `langgraph.json` directory.          |
| `--install-command TEXT` | N/A              | _(JS Only)_ Install command to run from the current directory.                 |
| `--help`                 | N/A              | Display the help message for this command.                                     |

### `langgraph up`

Starts the agent server and associated services locally using Docker.

**Usage:** `langgraph up [OPTIONS]`

| Option                         | Default                   | Description                                                                             |
| :----------------------------- | :------------------------ | :-------------------------------------------------------------------------------------- |
| `--wait`                       | N/A                       | Wait for all services to be fully started before the command exits. Implies `--detach`. |
| `--base-image TEXT`            | `langchain/langgraph-api` | Base image to use for the server.                                                       |
| `--image TEXT`                 | N/A                       | Use a pre-built Docker image directly, skipping the build step.                         |
| `--postgres-uri TEXT`          | N/A                       | A Postgres connection URI to use for the database instead of a local one.               |
| `--watch`                      | N/A                       | Automatically restart services when file changes are detected.                          |
| `--debugger-base-url TEXT`     | `http://127.0.0.1:[PORT]` | URL the debugger uses to access the agent API.                                          |
| `--debugger-port INTEGER`      | N/A                       | Serve the debugger UI on the specified port.                                            |
| `--verbose`                    | N/A                       | Show more detailed output from server logs.                                             |
| `-c`, `--config FILE`          | `langgraph.json`          | Path to the configuration file.                                                         |
| `-d`, `--docker-compose FILE`  | N/A                       | Path to an additional `docker-compose.yml` file to launch alongside the agent.          |
| `-p`, `--port INTEGER`         | `8123`                    | External port to expose the server on.                                                  |
| `--pull` / `--no-pull`         | `pull`                    | `--pull` to use the latest remote images; `--no-pull` to use local images.              |
| `--recreate` / `--no-recreate` | `no-recreate`             | `--recreate` forces recreation of containers even if unchanged.                         |
| `--help`                       | N/A                       | Display the help message for this command.                                              |

### `langgraph dockerfile`

Generates a `Dockerfile` based on the `langgraph.json` configuration.

**Usage:** `langgraph dockerfile [OPTIONS] SAVE_PATH`

| Argument    | Description                                                            |
| :---------- | :--------------------------------------------------------------------- |
| `SAVE_PATH` | **Required.** The path where the generated `Dockerfile` will be saved. |

| Option                | Default          | Description                                                     |
| :-------------------- | :--------------- | :-------------------------------------------------------------- |
| `-c`, `--config FILE` | `langgraph.json` | Path to the configuration file used to generate the Dockerfile. |
| `--help`              | N/A              | Show the help message for this command.                         |

## References

https://docs.langchain.com/langsmith/cli
