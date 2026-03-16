# Discord Webhook Proxy 方案調研

> 目標：找到能穿透 China GFW 的 Discord Webhook 轉發方案，比較各方案優劣。

## 背景

- `discord.com` / `discordapp.com` 自 2018 年起被 GFW 封鎖
- 在中國境內的服務需要透過代理才能發送 Discord Webhook
- 本項目 (Webhook-Distributor) 是一個 Flask 實現的 Webhook 轉發服務，部署在境外即可解決問題，但也值得了解其他更 elegant 的方案

---

## 現有開源項目

### 1. lewisakura/webhook-proxy

- **GitHub:** https://github.com/lewisakura/webhook-proxy
- **Tech Stack:** Node.js / TypeScript
- **原理:** 將 webhook URL 中的 `discord.com` 替換為 `webhook.lewisakura.moe`，代理轉發到 Discord
- **特點:**
  - 內建 Rate Limiting（5 req/2s）
  - 提供 `/queue` endpoint，保證投遞（soft limit 10/1s）
  - Discord 官方認可這類用途
  - 主要為 Roblox 社群設計
- **託管實例:** https://webhook.lewisakura.moe/
- **優點:** 最成熟的項目；直接替換 URL 即可使用
- **缺點:** 公共實例域名可能被 GFW 封鎖；自建需要 Node.js 環境

### 2. hyra-io/Discord-Webhook-Proxy

- **GitHub:** https://github.com/hyra-io/Discord-Webhook-Proxy
- **Tech Stack:** TypeScript, Express.js, MongoDB
- **原理:** HTTP 代理轉發，用 MongoDB 做分散式 Rate Limit 存儲
- **託管實例:** https://hooks.hyra.io/（部署在英國，Cloudflare 直連 + Argo）
- **優點:** 生產級品質；分散式 Rate Limiting；符合 Discord ToS
- **缺點:** 自建需要 MongoDB；託管域名可能被 GFW 封鎖

### 3. star-ot/simple-discord-webhooks-proxy

- **GitHub:** https://github.com/star-ot/simple-discord-webhooks-proxy
- **Tech Stack:** TypeScript on Vercel Serverless Functions
- **原理:** 一鍵部署到 Vercel，獲得代理 URL
- **優點:** 部署最簡單（一鍵）；免費；全球邊緣網路
- **缺點:** `*.vercel.app` 被 GFW SNI 封鎖 + DNS 污染，需自定義域名

### 4. darmiel/discord-webhook-proxy

- **GitHub:** https://github.com/darmiel/discord-webhook-proxy
- **Tech Stack:** Go + Go Template Engine
- **原理:** 通用 Webhook 格式轉換代理，用 Go Template 把任意格式轉成 Discord 格式
- **優點:** 極其靈活；可轉換任意 Webhook 格式；輕量 Go binary
- **缺點:** 配置較複雜；需要編寫 template

### 5. samuelcolvin/cloudflare-proxy

- **GitHub:** https://github.com/samuelcolvin/cloudflare-proxy
- **Tech Stack:** Cloudflare Worker (JavaScript)
- **原理:** 通用請求代理，透過 `upstream` 參數指定目標 URL，fire-and-forget 模式
- **優點:** 通用（不僅限 Discord）；免費；代碼極簡
- **缺點:** 無 Rate Limiting；非 Discord 專用

### 6. JRoy/disgit

- **GitHub:** https://github.com/JRoy/disgit
- **Tech Stack:** Cloudflare Worker 或 Docker
- **原理:** GitHub → Discord Webhook 增強格式化
- **優點:** 雙部署選項（Serverless / Docker）；豐富的 GitHub 事件格式化
- **缺點:** 僅限 GitHub 事件，非通用代理

---

## 雲端方案

### Cloudflare Workers + 自定義域名（最熱門免費方案）

- **免費額度:** 100,000 requests/day
- **實現:** ~20 行 Worker 腳本接收 POST → `fetch()` 轉發到 `discord.com/api/webhooks/...`
- **部署:** `wrangler` CLI 或 Cloudflare Dashboard 編輯器
- **示例代碼:**

```javascript
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const targetUrl = "https://discord.com" + url.pathname + url.search;

    const newRequest = new Request(targetUrl, {
      method: request.method,
      headers: request.headers,
      body: request.body,
    });

    return fetch(newRequest);
  }
};
```

- **注意:** `*.workers.dev` 默認域名在中國被封鎖，**必須綁定自定義域名**

### Vercel Serverless + 自定義域名

- **免費額度:** Hobby plan 足夠
- **實現:** Next.js API Route 或 Edge Function 代理
- **部署:** 可用 simple-discord-webhooks-proxy 一鍵部署
- **注意:** `*.vercel.app` 被封鎖，需自定義域名 + China-optimized DNS
  - A record → `76.223.126.88`
  - CNAME → `cname-china.vercel-dns.com`

### AWS Lambda + API Gateway

- **適合:** 企業級需求
- **實現:** Lambda 函數 + API Gateway 轉發
- **優點:** 穩定可靠；可部署在鄰近中國的區域（Tokyo / Singapore / Hong Kong）；API Gateway 內建 Rate Limiting
- **缺點:** 設定較複雜；需自定義域名避免封鎖

### 其他平台

| 平台 | 特點 |
|------|------|
| **Fly.io** | Docker 容器全球部署，免費層 $0-3/月 |
| **Railway** | 一鍵部署模板，自動配置 |
| **Netlify Edge Functions** | 基於 Deno Deploy，全球分佈 |

---

## GFW 封鎖現狀（重要）

| 域名/平台 | 封鎖狀態 | 備註 |
|-----------|---------|------|
| `discord.com` / `discordapp.com` | ❌ 已封鎖（2018 起） | 這就是需要代理的原因 |
| `*.workers.dev` | ❌ 大概率被封鎖 | 因 VPN 濫用，CF IP 段被加入黑名單 |
| `*.vercel.app` | ❌ 已封鎖 | SNI 封鎖 + DNS 污染 |
| 自定義域名（CF/Vercel） | ⚠️ 不確定 | 取決於域名是否被單獨針對 |
| 自建 VPS + 自定義域名 | ✅ 最可靠 | 完全自控，IP 被封可遷移 |
| Cloudflare Enterprise 中國網路 | ✅ 可用但需 ICP 備案 | 企業方案，不實際 |

**核心問題：** 沒有任何雲平台域名能保證在中國長期可用。GFW 在域名、SNI、IP 三個層面封鎖。

---

## 方案對比

| 方案 | 部署難度 | 成本 | 中國可用性 | Rate Limiting | 維護成本 |
|------|---------|------|-----------|---------------|---------|
| **CF Worker + 自定義域名** | 簡單 | 免費 | 可能（需自定義域名） | 需自建或用 CF Rate Limiting | 低 |
| **Vercel + 自定義域名** | 極簡（一鍵） | 免費 | 可能（需特殊 DNS） | 內建 | 低 |
| **境外 VPS 自建** | 中等（Docker） | $3-10/月 | 最佳（自控 IP/域名） | 需自建 | 中等 |
| **AWS Lambda + API GW** | 中等 | 近免費 | 良好（AP 區域） | 內建 | 低 |
| **公共代理（lewisakura 等）** | 零（換 URL） | 免費 | 不太可能（域名被封） | 內建 | 無 |
| **本項目 (Webhook-Distributor)** | 簡單（Docker） | VPS 費用 | 取決於部署位置 | 無 | 低 |

---

## 推薦方案（按可靠性排序）

### 🥇 方案一：境外 VPS + 自定義域名（最可靠）

部署本項目（或任意輕量代理）到 Hong Kong / Tokyo / Singapore 的 VPS：

- 完全控制 IP 和域名
- IP 被封可快速遷移
- 成本 $3-10/月（Vultr, DigitalOcean, Bandwagon 等）
- 可搭配 Cloudflare CDN 增加一層保護

**適合：** 穩定性要求高、願意花少量費用的場景

### 🥈 方案二：Cloudflare Worker + 自定義域名（最佳免費方案）

- 寫 ~20 行 Worker 代碼
- 綁定自己的域名（不用 `*.workers.dev`）
- 免費，100k requests/day
- 風險：CF 在中國的 IP 段日益受限

**適合：** 預算為零、請求量不大的場景

### 🥉 方案三：Vercel + 自定義域名 + China DNS

- 用 simple-discord-webhooks-proxy 一鍵部署
- 自定義域名 + Vercel China-optimized CNAME
- 免費，部署最簡單

**適合：** 追求最簡部署、可接受偶爾不穩定的場景

---

## 對本項目的改進建議

如果繼續使用 Webhook-Distributor，可以考慮：

1. **加入 Rate Limiting** — 防止被 Discord API 限流（Discord Webhook 限制：5 requests/2 seconds per webhook）
2. **加入重試機制** — 對 429 (Rate Limited) 響應自動重試
3. **支持異步轉發** — 用 `asyncio` + `aiohttp` 替代同步 `requests`，提升並發性能
4. **健康檢查 Endpoint** — 方便監控
5. **支持 Webhook URL 加密存儲** — 避免明文暴露 token
6. **Cloudflare Worker 版本** — 提供一個 CF Worker 實現，作為免費替代方案
