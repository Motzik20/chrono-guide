import { z, ZodSafeParseResult } from "zod";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL;

const globalErrorHandlers: Partial<Record<number, () => void>> = {
  401: () => {
    window.dispatchEvent(new CustomEvent("auth:unauthorized"));
  },
};

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly data?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiRequest<T>(
  endpoint: string,
  schema: z.ZodSchema<T>,
  options: RequestInit = {},
  customErrorHandlers?: Partial<Record<number, () => void>>
): Promise<T> {
  const isFormData = options.body instanceof FormData;

  const headers: Record<string, string> = {
    ...((options.headers as Record<string, string>) || {}),
  };

  const token = localStorage.getItem("chrono_token");
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  if (!isFormData && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  let json;
  try {
    const text = await response.text();
    json = text ? JSON.parse(text) : { detail: "Failed to parse response" };
  } catch {
    json = {
      detail: "Failed to parse response",
    };
  }

  if (!response.ok) {
    const status: number = response.status;
    if (customErrorHandlers?.[status]) {
      customErrorHandlers[status]();
    } else if (globalErrorHandlers[status]) {
      globalErrorHandlers[status]();
    }
    throw new ApiError(json.detail || "API error", status, json);
  }

  console.log("API response:", json);
  const result: ZodSafeParseResult<T> = schema.safeParse(json);

  if (!result.success) {
    console.error("Schema validation failed:", z.treeifyError(result.error));
    throw new ApiError(
      "Server response does not match expected format",
      422,
      result.error
    );
  }

  return result.data;
}
