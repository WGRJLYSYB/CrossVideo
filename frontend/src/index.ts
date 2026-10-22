interface Env {
  BACKEND_URL: string;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (!url.pathname.startsWith("/api/")) {
      return new Response("Not Found", { status: 404 });
    }

    try {
      const backendPath = url.pathname + url.search;

      // 复制请求头，去掉浏览器特有的头
      // 注意：不要手动设置 Host，运行时会根据 URL 自动设置
      const headers = new Headers(request.headers);
      headers.delete("Origin");
      headers.delete("Referer");

      const backendRequest = new Request(env.BACKEND_URL + backendPath, {
        method: request.method,
        headers: headers,
        body: request.body,
        redirect: "manual",
      });

      const response = await fetch(backendRequest);

      // 透传后端响应，加上 CORS 头
      const responseHeaders = new Headers(response.headers);
      responseHeaders.set("Access-Control-Allow-Origin", url.origin);

      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders,
      });
    } catch (error) {
      console.error("Proxy error:", error);
      return new Response(
        JSON.stringify({ error: error instanceof Error ? error.message : "Unknown error" }),
        {
          status: 502,
          headers: { "Content-Type": "application/json" },
        }
      );
    }
  },
};
