# 安全加固说明

## 本次变更
1. 新增 `ADMIN_API_KEY` 环境变量，用于保护 Tokens 管理接口。
2. `tokens` 相关接口默认不再匿名开放：
   - `GET /tokens`
   - `POST /tokens/upload`
   - `POST /tokens/clear`
   - `POST /tokens/error`
   - `GET /tokens/add/{token}`
   - `POST /seed_tokens/clear`
3. 增加 `/v1/models` 兼容接口，减少 OpenAI 客户端探测失败。
4. 启动日志与运行日志中的敏感信息已做脱敏处理（Token、代理凭证）。
5. 修复 `gateway/backend.py` 中 `token.startswith` 条件判断缺陷。

## 管理接口鉴权规则
优先使用 `ADMIN_API_KEY`：
- 请求头 `X-Admin-Key: <ADMIN_API_KEY>`
- 或 `Authorization: Bearer <ADMIN_API_KEY>`
- 或查询参数 `?admin_key=<ADMIN_API_KEY>`

当未设置 `ADMIN_API_KEY` 时，回退到 `AUTHORIZATION` 白名单校验。

当两者都未设置时，管理接口返回 `403`（默认关闭）。

## 建议部署配置
```bash
ADMIN_API_KEY=your-strong-admin-key
AUTHORIZATION=sk-your-api-key
```

## 页面使用方式
访问管理页时可直接带查询参数：
```text
/tokens?admin_key=your-strong-admin-key
```
