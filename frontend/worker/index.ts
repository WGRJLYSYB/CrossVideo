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

      // 逐个复制请求头，跳过 Host/Origin/Referer
      // 不含 Host 时，运行时会根据 BACKEND_URL 自动设置正确的 Host
      const headers = new Headers();
      for (const [key, value] of request.headers) {
        const lk = key.toLowerCase();
        if (lk === "host" || lk === "origin" || lk === "referer") continue;
        try {
          headers.append(key, value);
        } catch (e) {
          // 跳过其他禁止设置的头
        }
      }

      const backendRequest = new Request(env.BACKEND_URL + backendPath, {
        method: request.method,
        headers: headers,
        body: request.body,
        redirect: "manual",
      });

      const response = await fetch(backendRequest);

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
