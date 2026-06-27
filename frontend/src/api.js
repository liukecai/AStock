const base = import.meta.env.VITE_API_BASE_URL || "/api";

function buildHeaders(options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.adminSecret) {
    headers.set("X-Admin-Secret", options.adminSecret);
  }
  return headers;
}

async function request(path, options) {
  const response = await fetch(`${base}${path}`, {
    ...options,
    headers: buildHeaders(options),
  });
  if (!response.ok) {
    const message = await response.text();
    let parsed = null;
    try {
      parsed = JSON.parse(message);
    } catch {
      parsed = null;
    }
    throw new Error(parsed?.detail || parsed?.message || message || `请求失败：${response.status}`);
  }
  return response.json();
}

export const api = {
  getAdminAuthStatus: () => request("/admin/auth-status"),
  authorizeAdmin: (secret) => request("/admin/authorize", { method: "POST", adminSecret: secret }),
  dashboard: (page = 1, limit = 50, status = "全部", board = "全部") =>
    request(
      `/dashboard?page=${page}&limit=${limit}&status=${encodeURIComponent(status)}&board=${encodeURIComponent(board)}`
    ),
  stock: (symbol) => request(`/stocks/${symbol}`),
  runPipeline: (adminSecret = "") => request("/pipeline/run", { method: "POST", adminSecret }),
  getNewsLinks: (page = 1, limit = 50, symbol = "") => {
    let url = `/news-links?page=${page}&limit=${limit}`;
    if (symbol) url += `&symbol=${encodeURIComponent(symbol)}`;
    return request(url);
  },
  createNewsLink: (newsId, symbol, confidence = 1.0, matchType = "manual", adminSecret = "") =>
    request("/news-links", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      adminSecret,
      body: JSON.stringify({ news_id: newsId, symbol, confidence: parseFloat(confidence), match_type: matchType }),
    }),
  deleteNewsLink: (newsId, symbol, adminSecret = "") =>
    request(`/news-links?news_id=${encodeURIComponent(newsId)}&symbol=${encodeURIComponent(symbol)}`, {
      method: "DELETE",
      adminSecret,
    }),
  getRecentNews: (limit = 50) => request(`/news?limit=${limit}`),
  getEvents: (page = 1, limit = 50, commodity = "", eventType = "", direction = "") => {
    let url = `/events?page=${page}&limit=${limit}`;
    if (commodity) url += `&commodity=${encodeURIComponent(commodity)}`;
    if (eventType) url += `&event_type=${encodeURIComponent(eventType)}`;
    if (direction) url += `&direction=${encodeURIComponent(direction)}`;
    return request(url);
  },
  getEvent: (id) => request(`/events/${id}`),
  analyzeEvent: (title, summary = "", time = "", newsId = "", adminSecret = "") =>
    request("/events/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      adminSecret,
      body: JSON.stringify({ news_id: newsId, title, summary, time }),
    }),
  rebuildEvents: (adminSecret = "") => request("/events/rebuild", { method: "POST", adminSecret }),
  getJobs: () => request("/jobs"),
  retryJob: (name, adminSecret = "") =>
    request(`/jobs/${name}/retry`, { method: "POST", adminSecret }),
};

export const apiV2 = {
  // Graph API
  getEntity: (id) => request(`/v2/graph/entities/${encodeURIComponent(id)}`),
  getEntityNeighbors: (id, relationType = "") => {
    let url = `/v2/graph/entities/${encodeURIComponent(id)}/neighbors`;
    if (relationType) url += `?relation_type=${encodeURIComponent(relationType)}`;
    return request(url);
  },
  searchEntities: (q, entityType = "") => {
    let url = `/v2/graph/entities/search?q=${encodeURIComponent(q)}`;
    if (entityType) url += `&entity_type=${encodeURIComponent(entityType)}`;
    return request(url);
  },
  
  // Events API
  getEvents: (page = 1, pageSize = 20, eventType = "") => {
    let url = `/v2/events?page=${page}&page_size=${pageSize}`;
    if (eventType) url += `&event_type=${encodeURIComponent(eventType)}`;
    return request(url);
  },
  getEvent: (id) => request(`/v2/events/${encodeURIComponent(id)}`),
  getEventStocks: (id) => request(`/v2/events/${encodeURIComponent(id)}/stocks`),
  
  // Validation API
  getValidationEvent: (id) => request(`/v2/validation/events/${encodeURIComponent(id)}`),
  getValidationSummary: (type, key = "") => {
    let url = `/v2/validation/summary?summary_type=${encodeURIComponent(type)}`;
    if (key) url += `&key=${encodeURIComponent(key)}`;
    return request(url);
  },
  
  // Chat & Interactive API
  chatQuery: (query) => request("/v2/chat/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query })
  }),
  submitGraphFeedback: (relationId, action, details = "") => request(`/v2/graph/relations/${encodeURIComponent(relationId)}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, details })
  }),
  uploadPrivateText: (text) => request("/v2/input/upload", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text })
  })
};
