# Cloudflare Worker Discord Webhook Proxy 實現參考

> 最簡單的免費穿牆方案：用 Cloudflare Worker 做 Discord Webhook 代理

## 基本版：直接轉發

```javascript
// wrangler.toml:
// name = "discord-webhook-proxy"
// main = "src/index.js"
// compatibility_date = "2024-01-01"

export default {
  async fetch(request, env) {
    // 只接受 POST
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    // 從路徑中提取 webhook ID 和 token
    // 用法: https://your-domain.com/api/webhooks/{id}/{token}
    const url = new URL(request.url);
    const targetUrl = "https://discord.com" + url.pathname + url.search;

    const response = await fetch(targetUrl, {
      method: "POST",
      headers: {
        "Content-Type": request.headers.get("Content-Type") || "application/json",
      },
      body: request.body,
    });

    return new Response(response.body, {
      status: response.status,
      headers: {
        "Content-Type": response.headers.get("Content-Type") || "application/json",
      },
    });
  },
};
```

## 進階版：帶 Rate Limiting 和驗證

```javascript
export default {
  async fetch(request, env) {
    // CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
        },
      });
    }

    if (request.method !== "POST") {
      return new Response(JSON.stringify({ error: "Method not allowed" }), {
        status: 405,
        headers: { "Content-Type": "application/json" },
      });
    }

    const url = new URL(request.url);
    const path = url.pathname;

    // 驗證路徑格式：/api/webhooks/{id}/{token}
    const webhookPattern = /^\/api\/webhooks\/\d+\/[\w-]+$/;
    if (!webhookPattern.test(path)) {
      return new Response(JSON.stringify({ error: "Invalid webhook URL" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      });
    }

    const targetUrl = "https://discord.com" + path + url.search;
    const contentType = request.headers.get("Content-Type") || "application/json";

    try {
      const response = await fetch(targetUrl, {
        method: "POST",
        headers: { "Content-Type": contentType },
        body: request.body,
      });

      // 如果被 Discord rate limited，回傳 retry-after 資訊
      if (response.status === 429) {
        const retryAfter = response.headers.get("Retry-After");
        return new Response(
          JSON.stringify({
            error: "Rate limited by Discord",
            retry_after: retryAfter,
          }),
          {
            status: 429,
            headers: {
              "Content-Type": "application/json",
              "Retry-After": retryAfter || "5",
            },
          }
        );
      }

      return new Response(response.body, {
        status: response.status,
        headers: {
          "Content-Type": response.headers.get("Content-Type") || "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    } catch (err) {
      return new Response(JSON.stringify({ error: "Proxy error", detail: err.message }), {
        status: 502,
        headers: { "Content-Type": "application/json" },
      });
    }
  },
};
```

## 部署步驟

```bash
# 1. 安裝 wrangler CLI
npm install -g wrangler

# 2. 登入 Cloudflare
wrangler login

# 3. 初始化項目
wrangler init discord-webhook-proxy

# 4. 複製上面的代碼到 src/index.js

# 5. 部署
wrangler deploy

# 6. (重要) 綁定自定義域名
# 在 Cloudflare Dashboard → Workers → 你的 Worker → Settings → Domains & Routes
# 添加自定義域名路由（如 webhook.yourdomain.com/*）
```

## 使用方式

原本的 Discord Webhook URL：
```
https://discord.com/api/webhooks/123456789/abcdefg
```

替換為你的代理 URL：
```
https://webhook.yourdomain.com/api/webhooks/123456789/abcdefg
```

請求方式完全相同，只是域名不同。

## 多目標分發版（類似本項目功能）

```javascript
// 在 Worker 環境變數中設定多個目標 webhook
// wrangler.toml:
// [vars]
// WEBHOOKS = "https://discord.com/api/webhooks/111/aaa,https://discord.com/api/webhooks/222/bbb"

export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    const webhooks = (env.WEBHOOKS || "").split(",").filter(Boolean);
    if (webhooks.length === 0) {
      return new Response(JSON.stringify({ error: "No webhooks configured" }), {
        status: 500,
      });
    }

    const body = await request.text();
    const contentType = request.headers.get("Content-Type") || "application/json";

    // 並行發送到所有目標
    const results = await Promise.allSettled(
      webhooks.map((url) =>
        fetch(url.trim(), {
          method: "POST",
          headers: { "Content-Type": contentType },
          body: body,
        }).then((r) => ({ url: url.trim(), status: r.status }))
      )
    );

    const summary = results.map((r) =>
      r.status === "fulfilled"
        ? r.value
        : { url: "unknown", status: "error", reason: r.reason?.message }
    );

    return new Response(JSON.stringify(summary), {
      headers: { "Content-Type": "application/json" },
    });
  },
};
```

## 注意事項

- **必須用自定義域名**：`*.workers.dev` 在中國被封鎖
- **Discord Rate Limit**：每個 Webhook 限 5 requests / 2 seconds
- **Worker 免費限制**：100,000 requests/day，10ms CPU time/request
- **安全性**：考慮加入 API Key 驗證，防止代理被濫用
