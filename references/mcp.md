# MCP 调用参考与故障排查

## 已核对的服务事实

2026-10-04，作者对现有远程服务执行了 `initialize` → `notifications/initialized` → `tools/list`，未产生生图费用。

- MCP：`https://vps.wannian.fun/codex-image-mcp/mcp`
- 传输：Streamable HTTP；鉴权：Authorization Bearer（包内不含令牌）。
- 工具：`generate_image`。后端 `gpt-image-2-codex`，宿主固定 `gpt-6-luna`。
- 当前远程 schema 支持参考图；部分客户端或已有会话的包装 schema 可能仅暴露 `prompt` 和 `model`。调用以当次**模型可见的工具 schema**为准。
- 未发现 MCP resources / resourceTemplates；不要假设存在状态查询、图片检查或安装工具。

## generate_image 参数

| 参数 | 必需 | 服务当前支持的含义 |
| --- | --- | --- |
| `prompt` | 是* | 单条生图/改图要求（*若使用非空 `prompts` 则可与之配合） |
| `prompts` | 否 | 多条不同提示（1–4）；服务端批量并行时使用；有则优先于多次 tools/call |
| `n` | 否 | 同一 `prompt` 生成张数（1–4）；与多条 `prompts` 同时出现时以 `prompts` 为准 |
| `model` | 否 | 服务忽略该值，固定 gpt-6-luna；推荐省略 |
| `images` | 否 | 参考图数组：data URI/base64 字符串，或 `{data, mimeType}` / `{path}` 对象 |
| `image` | 否 | 单张参考图，同 images 的元素类型；勿与 `images` 重复传同一文件 |
| `image_path` | 否 | MCP 服务器本机图片路径或其支持的 sha256 标识；不是远程客户端本机路径 |

`n` / `prompts` 仅在当次 schema 公布时使用。未公布时不要假装批量已生效，改为串行单张调用。

`images` / `image` / `image_path` 仅在当次可见工具定义中存在时传入；选择一种输入形式即可。size、quality 自动处理，没有可直接设置的参数。

### 生图

```json
{
  "prompt": "Minecraft 风格的灵石物品图标，像素美术，青绿色晶体，主体居中，透明背景，无文字，无水印"
}
```

### 改图（仅当客户端暴露 images）

```json
{
  "prompt": "保留参考图主体与构图，将背景改为暖色秋日树林，不增加文字",
  "images": [
    {"data": "BASE64_OF_THE_USER_SELECTED_IMAGE", "mimeType": "image/png"}
  ]
}
```

示例中的 BASE64 是占位符，需本机读取用户指定图片的原始字节后编码；不能把字面量发给服务。也可使用 `data:image/png;base64,...`。不要在最终回复、日志或 Git 中展示大段 base64 或私有图像。

本机 Windows 图片路径并不会自动上传到 VPS。`C:/Users/.../image.png` 在远程服务器不存在；使用 data URI / data 对象传输原始图像。服务器本地路径只适用于图片确实位于 MCP 主机上且调用者有权访问的场景。

## 返回值与成功判定

不要固定假设返回值一定包含某个本地路径字段：客户端可能把 MCP 图片内容转换为附件、文件或图像对象。优先复用其原生返回附件，不猜测附件 URL。

成功判定是工具返回可用图片，并在需要落盘时核对实际文件。工具调用成功与 GUI 图片加载成功是两项证据。

## 故障排查

| 现象 | 检查和处理 |
| --- | --- |
| 工具不存在 | Skill 不能自动成为 MCP 工具；确认活动配置、刷新或新会话，按 setup 指南接入 |
| 401 / 403 | 凭据失效或没有服务权限；在本机更换凭据，不能索取/发布作者的令牌 |
| 404 / 非 MCP 响应 | 检查完整 `/codex-image-mcp/mcp` 地址与协议，不使用普通 API `/v1` 接口 |
| MCP 握手失败 | 检查客户端是否支持 Streamable HTTP、网络和代理，查看脱敏的客户端连接日志 |
| DSH 同名 namespace 错误 | 多个生效层重复注册了 codex-image；只保留真实活动入口，不重复安装 |
| size / quality 参数错误 | 删除未在当次 schema 公布的参数，将画面需求写进 prompt |
| 参考图找不到 | 客户端路径不在 VPS 上；改用 schema 支持的 data URI/base64，不上传无关文件 |
| `ENOENT ... realpath '/home/.../attachments/...'` 或 `C:\...` | Harness 与 MCP 不同机却传了本地路径。远程客户端必须 data URI；或在该 Harness 本机架路径内联桥。本台腾讯云桥仅覆盖本机，**新挂的 Harness 不会自动继承** |
| model 参数错误 | 不传 DeepSeek/Sol；通常省略 model，服务固定 gpt-6-luna |
| 超时 | 当前 DSH 示例为 180 秒；批量 `n`/`prompts` 时服务端应放大超时。先查是否已有结果，不要自动重复生成 |
| 有图片但看不到预览 | 检查真实图片请求、HTTP 状态和解码；不要仅依据附件无扩展名重新生成 |
| 多图很慢/很卡 | 多半是多次 tools/call 被串行。应改用一次 call 的 `n` 或 `prompts[]`（见 [server-mcp-changes.md](server-mcp-changes.md)）；低配机不要强开 MCP parallel |

不需要为了配置验证而发起生成请求。离线结构检查不等于远程调用测试，工具发现不等于图片已生成。

## 非目标

本包不包含远程 MCP 的部署代码、模型权重、平台访问令牌，也不依赖旧 wannian-luna-image 的本地 Python 程序。服务可用性、价格、访问权限和兼容客户端版本由各自提供方决定。远程服务改批量参数的清单见 [server-mcp-changes.md](server-mcp-changes.md)。
