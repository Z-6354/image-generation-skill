# Codex Image 技能包

**安装 Skill → 首次使用接入 MCP → 后续直接生图。**

把当前 `codex-image` 远程 MCP 的使用方式封装为可迁移 Agent Skill：自带首次接入指令、脱敏配置模板、真实参数说明，以及预览/下载规则。不需要本地 Python、Codex CLI 或模型权重。

> Skill 是指令，不是 MCP 运行时。客户端必须支持 Skills 和远程 MCP，并且用户需要自己的服务访问凭据。首次使用可由具备配置读写权限的 Agent 完成最小合并；客户端如需刷新/重启或用户填写凭据，仍需执行这一步。不能保证所有客户端零交互安装。

## 1. 下载并安装 Skill

DSH 已支持用户级 `~/.agents/skills/`；其他客户端使用其支持的 Skill 目录。如果系统已有同名 Skill，先备份/比较，不覆盖已有工作。

### Windows PowerShell（DSH 用户级）

```powershell
$dest = Join-Path $HOME '.agents/skills/codex-image'
if (Test-Path -LiteralPath $dest) { throw "目标已存在，请先备份或更新已有 Skill：$dest" }
New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent) | Out-Null
git clone https://github.com/Z-6354/image-generation-skill.git $dest
```

### macOS / Linux（DSH 用户级）

```sh
mkdir -p "$HOME/.agents/skills"
git clone https://github.com/Z-6354/image-generation-skill.git "$HOME/.agents/skills/codex-image"
```

也可在 GitHub 点击 Code → Download ZIP，解压后把整个包放到客户端的 Skill 目录中，确保 `codex-image/SKILL.md` 与 `references/`、`mcp/` 同级。只复制 SKILL.md 会丢失首次接入指南。

项目级 DSH 可放在项目 `.agents/skills/codex-image/` 下，避免用户级与项目级重复安装。安装后刷新 Skill 列表或开启新会话，确认可加载 `codex-image`。

## 2. 首次使用

告诉 Agent：

> 使用 codex-image Skill，帮我画一张橘猫坐在月亮上的儿童绘本插画。若 MCP 未接入，按技能包的首次接入指南配置；不要覆盖现有配置，凭据由我在本机填写。

Agent 会检查工具：

- 已存在 `generate_image`：立即按当前 schema 调用，不重复安装。
- 不存在：读取 [首次接入指南](references/setup.md)，识别客户端、合并模板、引导本机填写凭据，再刷新工具目录。
- 客户端不支持配置写入/热刷新：提供人工步骤；必要时开新会话后继续，不假装安装已生效。

默认 endpoint 为 `https://vps.wannian.fun/codex-image-mcp/mcp`。这不是无鉴权的公共生图服务；使用者应向服务管理员获取授权。远程服务会接收 prompt 与主动提交的参考图。可以换成兼容的自有服务，但参数以实际工具 schema 为准。

首次接入只需一次。之后每次以工具是否可见判断，不使用易过期的“已安装”标记。

## 3. 后续使用

> 使用 codex-image Skill，生成一张透明背景的 Minecraft 青绿色灵石物品图标，并提供预览和原图文件。

多图时优先一次工具调用：同提示用 `n`，不同文案/构图用 `prompts[]`（需远程 MCP 已实现，见 [references/server-mcp-changes.md](references/server-mcp-changes.md)）。不要靠并行多次 `generate_image` 加速——多数 DSH 会对 MCP 工具串行，低配机还会更卡。

Agent 会直接调用 MCP，并分别验证生成、文件提供和预览。宿主固定 `gpt-6-luna`、生图后端 `gpt-image-2-codex`；不跟随聊天模型切换。参考图能力受当前客户端暴露的参数限制；**远程 MCP 不能读取客户端本机路径**（Windows `C:\` 或异机 Linux 附件路径都会 `realpath` ENOENT），应传 data URI，或在该 Harness 本机架路径内联桥。

## 包内容

| 文件 | 用途 |
| --- | --- |
| [SKILL.md](SKILL.md) | 触发条件、按需接入、生图与交付规则 |
| [references/setup.md](references/setup.md) | DSH、Cursor 及其他客户端首次接入与卸载 |
| [references/mcp.md](references/mcp.md) | 已核对的工具参数、参考图与故障排查 |
| [references/server-mcp-changes.md](references/server-mcp-changes.md) | 远程 MCP 批量 `n` / `prompts[]` 修改清单 |
| [mcp/dsh.cordis.patch.example.yml](mcp/dsh.cordis.patch.example.yml) | DSH 脱敏连接模板 |
| [mcp/mcp.example.json](mcp/mcp.example.json) | 支持 mcpServers URL 的客户端模板 |
| [scripts/verify.py](scripts/verify.py) | 无网络、无生图费用的结构/泄密检查 |

## 验证与更新

```sh
python scripts/verify.py
```

验证 frontmatter、相对链接、模板、凭据泄漏和工作流关键约束；不需要第三方 Python 库。此脚本仅供维护/离线验证，日常使用 Skill 不要求安装 Python。

本包接入字段已与现有 DSH 配置和 MCP client schema 核对，远程工具定义已通过握手和 tools/list 确认。没有为发布而生成收费测试图片；新设备上的客户端接入、真实生图与 GUI 预览仍需分别验证。

更新时在已安装目录执行 `git pull --ff-only`，但先确认自己的修改已保留。本机 MCP 凭据放在客户端配置中，不放在技能仓库内，更新 Skill 不会替换那些配置。

## 边界与安全

- 这是 **Skill + 远程 MCP 接入包**，不是远程服务部署包，不包含服务源码或访问令牌。
- 不修改官方 Harness 源码，不新建替代服务器，不自动停止/重启宿主。
- 不包含旧 `wannian-luna-image` Python/API 方案；本包针对当前 codex-image MCP。
- 示例中只有 `REPLACE_WITH_YOUR_TOKEN` 占位符。请勿把真实凭据提交到 GitHub。
- 客户端、权限、网络或鉴权不满足时会引导配置，不能宣称所有设备自动即用。
- 超时可能仍有服务端执行结果，不自动重复调用以避免重复计费。

## 使用许可

本仓库自身的 Skill、文档、模板与验证脚本按 [MIT License](LICENSE) 发布。远程服务和模型的访问权限、价格及使用条款不由本许可授予。
