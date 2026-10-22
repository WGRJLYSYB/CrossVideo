// crossvideo Worker — /api/* 反向代理
// 只有 /api/ 开头的请求会进入这个 Worker（通过 wrangler 中的 run_worker_first 配置）
// 其他请求由 Cloudflare 直接返回静态资源，不经过 Worker

interface Env {
  BACKEND_URL: string;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname.startsWith("/api/")) {
      const backendPath = url.pathname + url.search;
      const backendRequest = new Request(env.BACKEND_URL + backendPath, request);

      try {
        const response = await fetch(backendRequest);
        return response;
      } catch (error) {
        return new Response(
          JSON.stringify({ error: "Backend service unavailable" }),
          {
            status: 502,
            headers: { "Content-Type": "application/json" },
          }
        );
      }
    }

    return new Response("Not Found", { status: 404 });
  },
};
