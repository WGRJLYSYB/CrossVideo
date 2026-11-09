import type { ExecutionContext } from '@cloudflare/workers-types';

// 1. 定义环境变量接口
export interface Env {
  BACKEND_URL: string; // 对应在 Cloudflare 后台或 wrangler.toml 中配置的环境变量
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    // 拦截 /api/ 开头的请求
    if (url.pathname.startsWith('/api/')) {
      // 2. 从环境变量中获取后端地址，如果没有配置则给一个默认的降级处理
      const targetBase = env.BACKEND_URL || 'https://api.yourbackend.com';

      const targetUrl = new URL(targetBase);
      targetUrl.pathname = url.pathname;
      targetUrl.search = url.search;

      const modifiedRequest = new Request(targetUrl, {
        method: request.method,
        headers: request.headers,
        body: request.body,
        redirect: request.redirect,
      });

      try {
        const response = await fetch(modifiedRequest);

        const newResponse = new Response(response.body, {
          status: response.status,
          statusText: response.statusText,
          headers: response.headers,
        });

        return newResponse;
      } catch (err: unknown) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        return new Response(JSON.stringify({ error: 'API Gateway Error', details: errorMessage }), {
          status: 502,
          headers: { 'Content-Type': 'application/json' },
        });
      }
    }

    return fetch(request);
  },
};