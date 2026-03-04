# `/v1/images/generations` 接口说明

## 已支持能力
- 路径：`POST /v1/images/generations`
- 鉴权：`Authorization: Bearer <Token>`
- 入参兼容（子集）：
  - `model`：可选，默认 `gpt-5-3`
  - `prompt`：必填
  - `n`：可选，默认 `1`，范围 `1~4`
  - `response_format`：仅支持 `url`
- 出参格式（OpenAI 风格）：
  - `{"created": <unix_ts>, "data": [{"url": "...", "revised_prompt": "..."}]}`

## 重要说明
- 当前实现复用 `/v1/chat/completions` 链路进行文生图，并从返回内容里提取图片 URL。
- 如果上游模型/账号在当前会话不支持图片生成，会返回 `502`，并附带上游响应预览，便于排查。

## 请求示例

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

