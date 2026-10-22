interface Env {
  BACKEND_URL: string;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname.startsWith("/api/")) {
      const backendPath = url.pathname + url.search;

      // 构造转发请求，修正 Host 头，去掉浏览器特有的头
      const backendUrl = new URL(env.BACKEND_URL + backendPath);
      const headers = new Headers(request.headers);
      headers.set("Host", backendUrl.host);  // 把 Host 改成后端的域名
      headers.delete("Origin");              // 去掉浏览器 Origin 头
      headers.delete("Referer");             // 去掉浏览器 Referer 头

      const backendRequest = new Request(backendUrl, {
        method: request.method,
        headers: headers,
        body: request.body,
        redirect: "manual",
      });

      try {
        const response = await fetch(backendRequest);

        // 加上 CORS 响应头，让浏览器允许跨域读取
        // 虽然 Worker 和前端同域，但显式设置更安全
        const responseHeaders = new Headers(response.headers);
        responseHeaders.set("Access-Control-Allow-Origin", url.origin);
        responseHeaders.set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
        responseHeaders.set("Access-Control-Allow-Headers", "Content-Type, Authorization");

        return new Response(response.body, {
          status: response.status,
          statusText: response.statusText,
          headers: responseHeaders,
        });
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
