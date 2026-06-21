const base = import.meta.env.VITE_API_BASE_URL || "/api";

async function request(path, options) {
  const response = await fetch(`${base}${path}`, options);
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `请求失败：${response.status}`);
  }
  return response.json();
}

export const api = {
  dashboard: () => request("/dashboard"),
  stock: (symbol) => request(`/stocks/${symbol}`),
  runPipeline: () => request("/pipeline/run", { method: "POST" }),
};

