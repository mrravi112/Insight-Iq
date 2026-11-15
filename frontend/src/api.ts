const rawApiBase = ((import.meta as any).env?.VITE_API_URL || "").trim().replace(/\/$/, "");
export const API_BASE = rawApiBase.endsWith("/api") ? rawApiBase.slice(0, -4) : rawApiBase;

function generateToken(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID().replace(/-/g, "") + "x";
  }
  const chars = "abcdefghijklmnopqrstuvwxyz0123456789";
  let res = "";
  for (let i = 0; i < 32; i++) {
    res += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return res;
}

export function getOwnerToken(): string {
  try {
    let t = localStorage.getItem("iq_token");
    if (!t || t.trim().length < 16) {
      t = generateToken();
      localStorage.setItem("iq_token", t);
    }
    return t.trim();
  } catch {
    return generateToken();
  }
}

export const token = getOwnerToken();

export class ApiError extends Error {
  status: number;
  constructor(m: string, s: number) {
    super(m);
    this.status = s;
  }
}

export async function api(path: string, opts: RequestInit = {}): Promise<any> {
  const ownerToken = getOwnerToken();
  const h: Record<string, string> = {
    "X-Owner-Token": ownerToken,
    ...((opts.headers as Record<string, string>) || {}),
  };

  // Set application/json only when sending non-FormData bodies
  if (opts.body && !(opts.body instanceof FormData) && !h["Content-Type"]) {
    h["Content-Type"] = "application/json";
  }
  // Let the browser set Content-Type with boundary for FormData
  if (opts.body instanceof FormData) {
    delete h["Content-Type"];
  }

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const targetUrl = `${API_BASE}/api${normalizedPath}`;

  let r: Response;
  try {
    r = await fetch(targetUrl, { ...opts, headers: h });
  } catch (netErr: any) {
    if (netErr instanceof ApiError) throw netErr;
    if (netErr?.name === "TypeError" && (netErr?.message?.includes("fetch") || netErr?.message?.includes("network"))) {
      throw new ApiError(
        "Unable to connect to the backend server. If using Render free tier, the backend may take 45-60 seconds to wake up from sleep. Please wait a moment and try again.",
        0
      );
    }
    throw new ApiError(netErr?.message || "Network request failed", 0);
  }

  if (!r.ok) {
    let m = r.statusText || `Request failed with status ${r.status}`;
    try {
      const j = await r.json();
      if (j && typeof j.detail === "string") {
        m = j.detail;
      } else if (j && j.detail) {
        m = JSON.stringify(j.detail);
      } else if (j && typeof j.message === "string") {
        m = j.message;
      }
    } catch {
      // Fallback to status text
    }
    throw new ApiError(m, r.status);
  }
  return r.status === 204 ? null : r.json();
}

export async function download(path: string, opts: RequestInit = {}, name: string) {
  const ownerToken = getOwnerToken();
  const h: Record<string, string> = {
    "X-Owner-Token": ownerToken,
    ...((opts.headers as Record<string, string>) || {}),
  };

  if (opts.body && !(opts.body instanceof FormData) && !h["Content-Type"]) {
    h["Content-Type"] = "application/json";
  }
  if (opts.body instanceof FormData) {
    delete h["Content-Type"];
  }

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const targetUrl = `${API_BASE}/api${normalizedPath}`;

  let r: Response;
  try {
    r = await fetch(targetUrl, { ...opts, headers: h });
  } catch (netErr: any) {
    if (netErr?.name === "TypeError" && (netErr?.message?.includes("fetch") || netErr?.message?.includes("network"))) {
      throw new ApiError(
        "Unable to download: cannot connect to backend server. The backend may be starting up.",
        0
      );
    }
    throw new ApiError(netErr?.message || "Download request failed", 0);
  }

  if (!r.ok) {
    let m = r.statusText || `Download failed with status ${r.status}`;
    try {
      const j = await r.json();
      m = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch {}
    throw new ApiError(m, r.status);
  }

  const u = URL.createObjectURL(await r.blob());
  const a = document.createElement("a");
  a.href = u;
  a.download = name;
  a.click();
  URL.revokeObjectURL(u);
}

export const C = {
  Positive: "var(--orange)",
  Neutral: "var(--neutral)",
  Negative: "var(--rose)"
} as Record<string, string>;
