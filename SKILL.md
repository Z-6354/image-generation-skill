---
name: codex-image
description: Generate or edit images, illustrations, icons, textures, GUI assets and pixel art through the codex-image MCP. On first use, guide or configure the MCP connection; on later uses, call the existing tool. Not for image inspection alone or the legacy wannian-luna Python API.
---

# Codex Image

通过远程 `codex-image` MCP 生图或改图。Skill 是工作指令；MCP 是实际工具连接，两者不能互相替代。

## 每次使用：先检查工具，缺失时才接入

1. 检查当前工具目录是否存在 `mcp__codex-image__generate_image`，或客户端等价命名的 `codex-image / generate_image`。
2. **存在：直接调用**，不要重装 MCP、索要已有凭据、运行初始化脚本或启动本地 Codex/Python 服务。
3. **不存在：只此时读取 [首次接入指南](references/setup.md)**。识别真实客户端和活动配置，用附带模板合并一个 MCP 连接；先读取现有配置，不覆盖其他服务，不修改官方源码。无法安全定位配置或没有凭据时，只询问缺失信息，不猜测。
4. 完成必要的客户端刷新/重启后重新检查工具。只有工具可用才进入生图步骤。不要声称“配置已写入”就等于“连接已成功”；若本会话工具目录无法刷新，明确让用户开启新会话后继续。

## 生图调用

以客户端当次公布的 schema 为准；详细参考见 [MCP 参数与故障排查](references/mcp.md)。远程 MCP 侧批量能力说明见 [server-mcp-changes.md](references/server-mcp-changes.md)。

### 已知坑：远程 MCP ≠ 本机附件路径（挂其他 Harness 必读）

远程 `codex-image` MCP 跑在 **VPS** 上。`images` / `image` / `image_path` 若传客户端本机路径（如 `C:\...`、`/home/.../.dsh/attachments/...`），会在 **MCP 主机** 上 `realpath`，常见报错：

`ENOENT: no such file or directory, realpath '...'`

这不是附件丢了，也不是 MCP 凭证坏了，而是 **Harness 与 MCP 不同机**。

| 场景 | 参考图怎么传 |
| --- | --- |
| MCP 与 DSH **同机**（如 VPS 本机 `127.0.0.1:3092`） | 可传该机附件路径 / `sha256:...` |
| **远程** Harness（Windows、另一台云机、新挂的 DSH 等）直连 `https://vps.wannian.fun/...` | **必须** data URI / `{data, mimeType}`，禁止传客户端本地路径 |
| **本台腾讯云 DSH**（已架 `127.0.0.1:3093` 桥） | 可传白名单本地路径，桥会内联后再转发；**别把「有桥」当成所有 Harness 的默认能力** |

**后续若再挂其他 Harness：** 默认按「远程客户端」处理——先确认有没有本机路径桥；没有桥就只传 data URI。不要照搬本台桥接配置，也不要假设 `~/.dsh/attachments` 路径在远程可读。

### 最小参数（单张）

```json
{
  "prompt": "一只圆滚滚的橘猫坐在月亮上，儿童绘本插画，柔和蓝紫背景，居中构图，无文字"
}
```

### 多图（优先一次 tools/call）

DSH 对 MCP 工具默认**独占串行**；低配客户端多路并行会更卡。按 schema 选用：

**同一提示词多变体**（schema 有 `n`）：

```json
{
  "prompt": "……画风与构图要求……",
  "images": ["<一份参考：data URI 或本机桥可解析路径>"],
  "n": 3
}
```

**多条不同提示词**（schema 有 `prompts`；贴合「不同气泡文案/姿势」）：

```json
{
  "prompts": ["构图A与文案A……", "构图B与文案B……", "构图C与文案C……"],
  "images": ["<一份参考>"]
}
```

若 schema **没有** `n` / `prompts`：改为逐张串行调用，并告知用户；不要假装已批量完成。

### 调用规则

- `prompt` / `prompts` 支持中文和英文；明确主体、风格、构图、用途、背景及禁止元素。
- 后端固定为 `gpt-image-2-codex`，宿主模型固定为 `gpt-6-luna`。通常**省略 model**，不要把聊天模型 DeepSeek/Sol 当作生图模型。
- 不要臆造 `size`、`quality`、`out`、`preset` 等未公布参数。尺寸/质量当前由服务自动处理；画面比例等需求写进 prompt，但不要承诺严格像素尺寸。
- **禁止**在同一步并行多个 `generate_image` 来“加速”；要用 `n` / `prompts` 或串行。
- 参考图只传**一份**字段（优先 `images: [一份]`）。不要把同一文件同时塞进 `images` 与 `image`。
- 改图只有在当前工具 schema 暴露参考图参数时使用。远程读不到客户端本机路径；无桥时必须 data URI / `{data, mimeType}`。
- 若当前工具只暴露 `prompt` / `model`，不要强行传 `images`；先说明不支持参考图参数。
- 如确需严格尺寸、透明通道或像素贴图，先检查产物，再按用户需求做独立后处理；明确区分原图与处理后的版本。

## 验证与交付

1. 工具失败、超时或只返回错误时，不声称已生成。检查结果中的图片附件或文件；落盘时确认存在、非空、能解码，需要时核对尺寸和模式。
2. 最终回复用 Markdown **内联预览**工具返回的图片：`![图片](<附件地址或图片路径>)`。多图时每张都预览。文件卡片不能代替内联预览。
3. 用户要求下载、保存、原图或指定格式时，如客户端支持 `present` / 文件交付工具，同时提供独立文件卡片；不把普通路径伪装成下载按钮。
4. 优先复用已有产物。附件无扩展名不是复制/重生成的理由。必须转存时仅复制原始字节，扩展名与实际格式一致，并核对前后 SHA-256。
5. Windows Markdown 目标用 `/` 代替 `\\`，目标包在 `<…>` 内；编码路径中的字面量 `%`、`#`、`?`。
6. 区分“已生成”“已提供文件”“已验证 GUI 预览/下载”。预览失败先查实际请求路径、HTTP 状态与解码结果。

## 安全与边界

- 本包不携带访问凭据，也不部署远程 MCP 服务。首次接入需要用户有可用 MCP 地址和授权。
- 密钥仅留在本机安全配置；不得写入 Skill、示例、Git、公开日志或最终回复。
- 不主动生成付费测试图片作为安装验收；工具发现足以确认接入。
- 超时不代表服务端未执行；先查已有结果，不自动连续重试，避免重复计费。
- 只看图/验收现有图时使用读图工具，不调用生图。旧 `wannian-luna-image` 不是默认回退。

## 触发核对

- “画一张海报 / 生成 Minecraft 图标 / 用这张图改背景” → 检查 MCP，再生成或按 schema 改图。
- “按这个风格多生成几张（同提示）” → 一次 call + `n`（若有）；否则串行并说明。
- “几张不同文案/构图” → 一次 call + `prompts[]`（若有）；否则串行。
- “第一次用这个 Skill，MCP 没装” → 读取接入指南，只配置一次。
- “看看这张图片尺寸” → 读图检查，不生成。
- “使用旧 wannian-luna API” → 不强行切换到本 Skill。
