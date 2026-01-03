import { z, ZodSafeParseResult } from "zod";

function getBaseUrl(): string {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL;

  if (!baseUrl) {
    throw new Error(
      "NEXT_PUBLIC_API_URL is not set. Please set it in your .env.local file or environment variables."
    );
  }
  return baseUrl;
}

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

function buildHeaders(options: RequestInit = {}): Record<string, string> {
  const headers: Record<string, string> = {
    ...((options.headers as Record<string, string>) || {}),
  };
  return headers;
}

export async function apiDownloadRequest(
  endpoint: string,
  options: RequestInit = {}
): Promise<void> {
  const headers = buildHeaders(options);
  const baseUrl = getBaseUrl();
  const response = await fetch(`${baseUrl}${endpoint}`, {
    ...options,
    headers,
    credentials: "include",
  });

  if (!response.ok) {
    const status: number = response.status;
    if (globalErrorHandlers[status]) {
      globalErrorHandlers[status]();
      return;
    }
    const errorText = await response.text();
    let errorJson;
    try {
      errorJson = JSON.parse(errorText);
    } catch {
      errorJson = { detail: "Failed to download file" };
    }
    throw new ApiError(
      errorJson.detail || "Failed to download file",
      status,
      errorJson
    );
  }

  const contentDisposition = response.headers.get("Content-Disposition");
  let filename = "download";
  if (contentDisposition) {
    filename = contentDisposition.split("filename=")[1] || "schedule.ics";
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();

  URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

export async function apiRequest<T>(
  endpoint: string,
  schema: z.ZodSchema<T> | undefined,
  options: RequestInit = {},
  customErrorHandlers?: Partial<Record<number, () => void>>
): Promise<T> {
  const isFormData = options.body instanceof FormData;
  const baseUrl = getBaseUrl();
  const headers = buildHeaders(options);

  if (!isFormData && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  const response = await fetch(`${baseUrl}${endpoint}`, {
    ...options,
    headers,
    credentials: "include",
  });

  let json;
  try {
    const text = await response.text();
    console.log("API response:", text);
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
  if (!schema) {
    return undefined as T;
  }
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
