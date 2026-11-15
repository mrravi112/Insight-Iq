export const token = (() => {
  let t = localStorage.getItem("iq_token");
  if (!t) {
    t = crypto.randomUUID().replace(/-/g, "") + "x";
    localStorage.setItem("iq_token", t);
  }
  return t;
})();

export class ApiError extends Error {
  status: number;
  constructor(m: string, s: number) {
    super(m);
    this.status = s;
  }
}

export async function api(path: string, opts: RequestInit = {}): Promise<any> {
  const h: any = { "X-Owner-Token": localStorage.getItem("iq_token") || token, ...(opts.headers || {}) };
  if (opts.body && !(opts.body instanceof FormData)) h["Content-Type"] = "application/json";
  const r = await fetch("/api" + path, { ...opts, headers: h });
  if (!r.ok) {
    let m = r.statusText;
    try {
      const j = await r.json();
      m = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch {}
    throw new ApiError(m, r.status);
  }
  return r.status === 204 ? null : r.json();
}

export async function download(path: string, opts: RequestInit, name: string) {
  const r = await fetch("/api" + path, {
    ...opts,
    headers: { "X-Owner-Token": localStorage.getItem("iq_token") || token, "Content-Type": "application/json" }
  });
  if (!r.ok) {
    let m = r.statusText;
    try { m = (await r.json()).detail; } catch {}
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
