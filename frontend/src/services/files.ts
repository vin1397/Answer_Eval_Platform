import api from "../services/api";

/**
 * Fetches a protected file (answer script, question paper) as an object URL
 * so it can be rendered inline in a viewer. Axios attaches the JWT header;
 * the resulting URL must be revoked by the caller when done.
 */
export async function fetchProtectedFileUrl(path: string): Promise<string> {
  const res = await api.get(path, { responseType: "blob" });
  const contentType = res.headers["content-type"];
  return window.URL.createObjectURL(
    new Blob([res.data], { type: typeof contentType === "string" ? contentType : "application/octet-stream" })
  );
}

export function revokeObjectUrl(url: string | null) {
  if (url) window.URL.revokeObjectURL(url);
}
