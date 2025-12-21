import { z } from "zod";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL;

export async function apiRequest<T>(
  endpoint: string,
  schema: z.ZodSchema<T>,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  const json = await response.json();

  if (!response.ok) {
    throw new Error(json.detail || "API error");
  }

  const result = schema.safeParse(json);

  if (!result.success) {
    console.error("Schema validation failed:", z.treeifyError(result.error));
    throw new Error("Server response does not match expected format");
  }

  return result.data;
}