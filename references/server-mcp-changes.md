# 远程 MCP 需要修改的内容（给服务器维护者）

面向 `https://vps.wannian.fun/codex-image-mcp/mcp`（或同机 `127.0.0.1:3092`）的 **codex-image** 服务。客户端 DSH 与 MCP 经常**不同机**；低配客户端上多路 `tools/call` 会被串行，且内存紧张。

## 必须改

### 1. 参数 `n`（同提示多变体）

| 项 | 要求 |
| --- | --- |
| 类型 | integer，1–4，默认 1 |
| 语义 | 同一 `prompt` + 同一份参考图，服务端并发生成 n 张 |
| 参考图 | **只解析/上传一次**，再复用 |
| 返回 | n 个 image content block，全部可预览 |
| 超时 | 随 n 放大，例如 `min(600s, 180 + 90*(n-1))` |
| 并发 | 服务端有限池，建议 max 4 |

### 2. 参数 `prompts`（不同提示词批量）— 强烈建议

| 项 | 要求 |
| --- | --- |
| 类型 | `string[]`，长度 1–4 |
| 语义 | 多条不同提示（不同文案/构图），共享同一份参考图 |
| 与 `n` | `prompts.length > 1` 时忽略 `n`；仅 `prompt` + `n` 用于同句多变体 |
| 返回 | 与 prompts 条数对应的多张图 |

真实客户端常会为「同一画风、不同气泡文案」发多次不同 `prompt`；没有 `prompts[]` 就只能多次 call，墙钟≈单张×次数。

### 3. 工具 description

写明：

- 同提示多图用 `n`
- 不同提示用 `prompts[]`
- **不要**依赖客户端并行多次 `generate_image`
- 远程客户端参考图用 data URI；同机才可传本机路径

### 4. 参考图去重

若同时收到相同的 `images[]` 与 `image`，只保留一份，避免 “Used 2 reference image(s)” 重复计费/重复编码。

## 不要改（除非另有需求）

- 鉴权方式（Bearer）与公网 URL 可保持不变
- 不必为解决路径问题去读腾讯云 DSH 磁盘（客户端侧用桥或 data URI）
- 不必要求客户端打开 MCP 工具 parallel（低配机不安全）

## 验收

1. `tools/list` 可见 `n`，建议可见 `prompts`
2. `generate_image({ prompt, n: 3 })` 墙钟接近单张，返回 3 张图
3. `generate_image({ prompts: [a,b,c], images: [一份] })` 返回 3 张不同图
4. 重复的 `image`+`images` 同文件只按 1 份参考处理

## 伪代码

```js
async function generate_image(args) {
  const refs = uniqueRefs(args.images, args.image, args.image_path)
  const jobs = args.prompts?.length > 1
    ? args.prompts.slice(0, 4).map((prompt) => runOne({ prompt, refs }))
    : Array.from({ length: clamp(args.n ?? 1, 1, 4) }, () =>
        runOne({ prompt: args.prompt, refs }))
  const outs = await mapPool(jobs, 4)
  return { content: outs.flatMap(toImageBlocks) }
}
```
