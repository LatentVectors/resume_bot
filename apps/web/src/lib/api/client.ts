/**
 * Base API client for making requests to the Next.js API routes.
 */

/**
 * Custom error class for API errors.
 */
export class APIError extends Error {
  status: number;
  statusText: string;
  detail?: string;
  fieldErrors?: Record<string, string[]>;

  constructor(
    status: number,
    statusText: string,
    detail?: string,
    fieldErrors?: Record<string, string[]>
  ) {
    super(detail || `API error: ${status} ${statusText}`);
    this.name = "APIError";
    this.status = status;
    this.statusText = statusText;
    this.detail = detail;
    this.fieldErrors = fieldErrors;
  }
}

/**
 * Type guard to check if a value is an API error response.
 */
function isAPIErrorResponse(value: unknown): value is {
  error: string;
  details?: Record<string, unknown>;
} {
  return (
    typeof value === "object" &&
    value !== null &&
    "error" in value &&
    typeof (value as { error: unknown }).error === "string"
  );
}

/**
 * Makes a typed API request to the Next.js API routes.
 *
 * @param endpoint - API endpoint path (e.g., "/api/jobs")
 * @param options - Fetch options (method, body, headers, etc.)
 * @returns Promise resolving to the typed response data
 * @throws APIError if the request fails
 */
export async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(endpoint, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });
  } catch (error) {
    // Handle network errors (connection refused, timeout, etc.)
    const errorMessage =
      error instanceof Error ? error.message : "Network error";
    throw new APIError(
      0,
      "Network Error",
      `Failed to connect to API: ${errorMessage}`
    );
  }

  // Handle 204 No Content responses (e.g., DELETE operations)
  if (response.status === 204) {
    return undefined as T;
  }

  // Handle error responses
  if (!response.ok) {
    let detail: string | undefined;
    let fieldErrors: Record<string, string[]> | undefined;

    try {
      const errorData = await response.json();
      if (isAPIErrorResponse(errorData)) {
        detail = errorData.error;
        // Handle validation errors with details.fieldErrors
        if (
          errorData.details &&
          typeof errorData.details === "object" &&
          "fieldErrors" in errorData.details
        ) {
          fieldErrors = errorData.details.fieldErrors as Record<string, string[]>;
        }
      }
    } catch {
      // If response is not JSON, use status text as detail
      detail = response.statusText;
    }

    throw new APIError(
      response.status,
      response.statusText,
      detail,
      fieldErrors
    );
  }

  // Parse JSON response
  try {
    const data = await response.json();
    return data as T;
  } catch {
    // If response is not JSON, throw an error
    throw new APIError(
      response.status,
      response.statusText,
      "Invalid JSON response from server"
    );
  }
}
