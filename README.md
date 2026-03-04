# CHAT2API

🤖 一个将 ChatGPT Web 能力转换为 OpenAI 兼容 API 的代理服务（现用增强版）

🌟 支持免登录 `GPT-3.5`（受 IP/地区策略影响）

💥 支持 `AccessToken` / `RefreshToken`，支持 `GPT-4/4o/mini`、`GPT-5*`、`O1/O3`、`GPTs`

🔍 `/v1/models` 支持实时拉取上游模型列表，失败自动回退静态列表

🖼️ 新增 `/v1/images/generations` 兼容端点（OpenAI 子集）

👮 Tokens 管理接口已增加 `ADMIN_API_KEY` 校验，默认更安全


## 交流群

[https://t.me/chat2api](https://t.me/chat2api)

提问前请先阅读文档，尤其是常见问题。

建议提问时附上：

1. 启动日志截图（敏感信息打码）
2. 报错日志（敏感信息打码）
3. 请求路径、状态码和响应体


## 功能

### 最新版本号存于 `version.txt`

### 逆向 API 功能
> - [x] 流式、非流式传输
> - [x] 免登录 `GPT-3.5` 对话
> - [x] `GPT-4/4o/mini`、`O1/O3`、`GPTs` 对话
> - [x] `GPT-5*` 模型直通（不再被降级为 `gpt-4o`）
> - [x] 上传图片、文件（支持 URL 和 base64）
> - [x] `/v1/models` 实时拉取上游模型 + 60 秒缓存 + 静态回退
> - [x] `/v1/images/generations`（兼容子集：`model/prompt/n/response_format=url`）
> - [x] 多账号轮询，支持 `AccessToken` 与 `RefreshToken`
> - [x] Tokens 管理（上传、清除、查看异常 token）
> - [x] 非重试类 4xx（400/401/403/404/422）直接返回，减少无效重试

### 官网镜像功能
> - [x] 支持官网原生镜像
> - [x] 后台账号池随机抽取，`Seed` 可绑定会话
> - [x] 支持 `RefreshToken` 或 `AccessToken` 登录
> - [x] 支持 `GPTs` 商店与官网多语言切换
> - [x] 可通过 `ENABLE_GATEWAY=true` 启用镜像模式

> TODO
> - [ ] 欢迎提 issue


## 本仓库现用版本改动

1. 模型列表：`GET /v1/models` 改为优先实时查询上游 `backend-api/models`，失败自动回退静态模型，兼容探测型客户端。
2. 模型映射：`gpt-5*` 系列模型保持透传，避免误降级。
3. 图片生成：新增 `POST /v1/images/generations`，兼容 OpenAI 请求/响应格式（子集）。
4. 稳定性：对非重试类 4xx 错误直接返回，避免重复请求放大故障。
5. 安全性：Tokens 管理接口新增 `ADMIN_API_KEY` 校验逻辑，降低误暴露风险。


## 逆向 API

完全 `OpenAI` 风格的接口，支持传入 `AccessToken` 或 `RefreshToken`。

### 1) 对话接口

```bash
curl --location 'http://127.0.0.1:5005/v1/chat/completions' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer {{Token}}' \
--data '{
  "model": "gpt-5-mini",
  "messages": [{"role":"user","content":"Say this is a test!"}],
  "stream": true
}'
```

### 2) 模型列表接口

```bash
curl --location 'http://127.0.0.1:5005/v1/models' \
--header 'Authorization: Bearer {{Token}}'
```

### 3) 图片生成接口（兼容子集）

```bash
curl --location 'http://127.0.0.1:5005/v1/images/generations' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer {{Token}}' \
--data '{
  "model": "gpt-5-3",
  "prompt": "a cyberpunk corgi riding a motorcycle at sunset",
  "n": 1,
  "response_format": "url"
}'
```

将你账号的 `AccessToken` 或 `RefreshToken` 作为 `{{Token}}` 传入。

若有 Team 账号，可传入 `ChatGPT-Account-ID`：

- 方式一：在请求头传 `ChatGPT-Account-ID`
- 方式二：`Authorization: Bearer <AccessToken或RefreshToken>,<ChatGPT-Account-ID>`

> - `AccessToken` 获取：登录 chatgpt 后访问 [https://chatgpt.com/api/auth/session](https://chatgpt.com/api/auth/session) 读取 `accessToken`
> - `RefreshToken`：本仓库不提供获取方法
> - 免登录 `GPT-3.5` 无需传 Token（可用性受网络环境影响）

图片接口详细说明见 [docs/images-api.md](docs/images-api.md)。


## Tokens 管理

1. 建议配置 `ADMIN_API_KEY` 后再开放管理端接口。
2. 访问 `/tokens`（或 `/{api_prefix}/tokens`）可查看和上传 Tokens。
3. 管理端校验优先级：
   - 若设置了 `ADMIN_API_KEY`，需提供匹配值（支持 `x-admin-key`、`admin_key`、表单 `admin_key` 或 Bearer）
   - 若未设置 `ADMIN_API_KEY`，回退使用 `AUTHORIZATION` 列表校验
   - 两者都未配置时，管理接口返回 `403`

![tokens.png](docs/tokens.png)


## 官网原生镜像

1. 设置 `ENABLE_GATEWAY=true` 并重启服务。
2. 在 Tokens 管理页面上传 `RefreshToken` 或 `AccessToken`。
3. 访问 `/login` 进入登录页。

![login.png](docs/login.png)

4. 进入官网镜像页面使用。

![chatgpt.png](docs/chatgpt.png)


## 环境变量

每个变量都有默认值。若不确定含义，建议保持默认。

| 分类 | 变量名 | 示例值 | 默认值 | 描述 |
|---|---|---|---|---|
| 安全相关 | API_PREFIX | `your_prefix` | `None` | API 前缀，设置后请求路径需带前缀 |
|  | AUTHORIZATION | `sk-a,sk-b` | `[]` | 自定义授权码列表（逗号分隔） |
|  | ADMIN_API_KEY | `change-me` | `None` | Tokens 管理接口专用管理密钥（推荐设置） |
|  | AUTH_KEY | `your_auth_key` | `None` | 网关模式可选鉴权 key |
| 请求相关 | CHATGPT_BASE_URL | `https://chatgpt.com` | `https://chatgpt.com` | 上游地址，支持逗号分隔多地址 |
|  | PROXY_URL | `http://ip:port` | `[]` | 全局代理，支持多个 |
|  | EXPORT_PROXY_URL | `http://ip:port` | `None` | 出口代理（文件/图片下载场景） |
| 功能相关 | HISTORY_DISABLED | `true` | `true` | 是否禁用历史记录 |
|  | RETRY_TIMES | `3` | `3` | 失败重试次数 |
|  | ENABLE_LIMIT | `true` | `true` | 是否启用官方限制保护 |
|  | SCHEDULED_REFRESH | `false` | `false` | 定时刷新 AccessToken |
|  | RANDOM_TOKEN | `true` | `true` | 是否随机选 token |
| 网关相关 | ENABLE_GATEWAY | `false` | `false` | 是否启用官网镜像功能 |
|  | AUTO_SEED | `true` | `true` | 是否启用随机 seed 模式 |
|  | FORCE_NO_HISTORY | `false` | `false` | 网关模式下强制无历史 |
|  | NO_SENTINEL | `false` | `false` | 关闭 sentinel 流程（仅排障时使用） |

完整变量可参考 `utils/configs.py` 与 `.env.example`。


## 部署

### 直接部署

```bash
git clone https://github.com/onebu123/chatgpt2api
cd chatgpt2api
pip install -r requirements.txt
python app.py
```

### Docker 部署

```bash
docker run -d \
  --name chat2api \
  -p 5005:5005 \
  lanqian528/chat2api:latest
```

### Docker Compose（推荐）

```bash
mkdir chat2api
cd chat2api
wget https://raw.githubusercontent.com/onebu123/chatgpt2api/main/docker-compose-warp.yml
docker-compose up -d
```


## 常见问题

> - 错误码说明：
>   - `401`：鉴权失败或 Token 无效
>   - `403`：权限不足（例如管理接口密钥不匹配）
>   - `429`：请求频率受限
>   - `500`：服务内部异常
>   - `502`：上游不可用或能力未开通

> - 为什么 `/v1/images/generations` 返回 502？
>   - 常见原因是上游账号/会话没有图片工具权限，而非接口格式错误。

> - 为什么客户端模型列表和实际可用模型不一致？
>   - `/v1/models` 已优先实时拉取上游；若上游失败会回退静态列表，属于保护性降级。

> - 环境变量 `AUTHORIZATION` 是什么？
>   - 是你给本服务设置的访问密钥（可多值），用于调用轮询 token 能力。


## License

MIT License
