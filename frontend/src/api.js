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
  dashboard: (page = 1, limit = 50, status = "全部", board = "全部") =>
    request(
      `/dashboard?page=${page}&limit=${limit}&status=${encodeURIComponent(status)}&board=${encodeURIComponent(board)}`
    ),
  stock: (symbol) => request(`/stocks/${symbol}`),
  runPipeline: () => request("/pipeline/run", { method: "POST" }),
  getNewsLinks: (page = 1, limit = 50, symbol = "") => {
    let url = `/news-links?page=${page}&limit=${limit}`;
    if (symbol) url += `&symbol=${encodeURIComponent(symbol)}`;
    return request(url);
  },
  createNewsLink: (newsId, symbol, confidence = 1.0, matchType = "manual") =>
    request("/news-links", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ news_id: newsId, symbol, confidence: parseFloat(confidence), match_type: matchType }),
    }),
  deleteNewsLink: (newsId, symbol) =>
    request(`/news-links?news_id=${encodeURIComponent(newsId)}&symbol=${encodeURIComponent(symbol)}`, {
      method: "DELETE",
    }),
  getRecentNews: (limit = 50) => request(`/news?limit=${limit}`),
};
