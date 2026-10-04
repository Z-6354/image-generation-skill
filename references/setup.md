# 首次接入 MCP（仅工具缺失时读取）

## 目标与前提

实现一次接入，后续直接调用。远程 MCP 不需要在用户电脑安装 Python、Codex CLI 或本地生图服务；“安装 MCP”在此指给现有客户端注册远程连接。

默认服务地址：`https://vps.wannian.fun/codex-image-mcp/mcp`，传输协议为 **Streamable HTTP**。这是作者当前使用的远程服务，不保证对所有用户开放或永久免费。用户需要向服务管理员获取访问凭据，也可提供兼容的其他服务地址。默认地址会接收 prompt 和用户主动上传的参考图，使用前应知晓这条数据流。

## Agent 按需接入步骤

1. 先检查真实工具目录，已有 `codex-image` 的 `generate_image` 就结束安装，直接使用。
2. 判断当前是 DSH、Cursor 还是其他客户端；只读检查活动配置。不能凭当前目录猜测客户端。已有相同服务名时检查/修复它，不重复注册。
3. 确认用户要使用的服务地址、凭据是否已在本机配置。没有凭据时请用户在本机客户端安全设置中填写，避免把密钥贴到公开对话。**占位符不是有效令牌**。
4. 能识别客户端且当前请求授权接入时，可读取附带模板，先备份现有配置，再做最小合并。没有文件权限或不支持运行时重载时提供人工步骤，不绕过权限、不停止服务、不自动重启用户正在使用的实例。
5. 使用客户端支持的刷新/重连；需要重启时提前说明，由用户确认操作。在新会话中复查 `generate_image` 的工具定义；允许客户端刷新工具目录时无需重启。
6. 安装验收只做工具发现，不生成收费测试图片。真实首个生图请求再生成。

不要以本地“已安装”标记代替工具检查：设备迁移、凭据失效、服务离线后标记会失真。工具已存在不表示请求必然成功；首次调用仍需处理鉴权/超时错误。

## DSH

通过当前运行环境的 `DSH_PROFILE_DIR` 定位活动 profile；缺失时让用户确认，**不要硬编码 desktop/web**。模板为 [DSH 配置模板](../mcp/dsh.cordis.patch.example.yml)。

将模板中的 insert 项合并到活动 profile 的 `cordis.patch.yml` 顶层列表；保留所有已有条目。如果已有 `serverName: codex-image`，编辑现有条目，不再新增同名实例。如果插件位于其他加载层，先确认真正生效的来源，避免在多个层重复注册。

```yaml
- insert:
    - id: mcp-codex-image
      name: "@deepseek-ai/dsh-mcp-client"
      config:
        serverName: codex-image
        transport: streamable-http
        url: https://vps.wannian.fun/codex-image-mcp/mcp
        headers:
          Authorization: "Bearer REPLACE_WITH_YOUR_TOKEN"
        toolCallTimeoutMs: 180000
```

在本地填写自己的令牌；此配置可能包含明文凭据，限制访问权限且不要提交。这里的占位符需要实际替换，**不假设 DSH 会自动展开环境变量表达式**。不要覆盖 profile 的 package.json 或 cordis 配置，也不用改官方 Harness 源码。

当前 DSH 需要能解析 `@deepseek-ai/dsh-mcp-client`。若报插件不存在，先检查当前版本是否提供该插件；根据该版本的官方安装方法启用，不能盲目升级/改写官方依赖。恢复连接或按现有客户端流程重启后，开新会话检查工具名 `mcp__codex-image__generate_image`。此配置格式已与作者现有 profile 和 MCP client 配置定义核对；不同版本以当前客户端 schema 为准。

## Cursor / 支持 mcpServers URL 的客户端

模板为 [MCP JSON 模板](../mcp/mcp.example.json)。在 Cursor 的 MCP 设置中编辑配置；常见用户级位置为 `~/.cursor/mcp.json`，项目级为 `.cursor/mcp.json`。先查现有服务所在层，选择一个作用域，不要在两层重复定义。

```json
{
  "mcpServers": {
    "codex-image": {
      "url": "https://vps.wannian.fun/codex-image-mcp/mcp",
      "headers": {
        "Authorization": "Bearer REPLACE_WITH_YOUR_TOKEN"
      }
    }
  }
}
```

仅合并 `mcpServers.codex-image`；不要用模板覆盖整个文件。本机填入凭据，刷新 MCP 并检查 `generate_image` 已出现。版本若不支持远程 URL，应使用其官方远程 MCP 接入方式，不把 HTTP endpoint 当作 stdio executable。

## 其他客户端

使用客户端官方远程 MCP 设置：服务名 `codex-image`、URL 为上述 `/mcp` 地址、Streamable HTTP、Authorization Bearer、自定义超时建议 180 秒。不同产品配置结构和工具命名不同，JSON 模板不是所有产品的通用可直接复制格式。

先检查官方 UI/本机 schema 再配置；不能假装 Skill 有能力给不支持 MCP 的客户端添加工具。如果产品不支持远程 MCP 或 Agent 无权配置，明确说明限制，交由用户在受支持的客户端完成接入。

## 安装完成的证据

- 地址与协议正确，客户端连接成功。
- `tools/list` 或工具目录包含 `generate_image`，其必需参数为 `prompt`。
- Agent 能在新/刷新后的会话发现该工具。

以上只确认 MCP 接入，不证明生图、预览或保存已成功；这些在用户真实请求中分别验证。

## 挂其他 Harness 时的路径坑（必读）

直连远程 MCP（`https://vps.wannian.fun/codex-image-mcp/mcp`）时，**不要**把该 Harness 本机的附件路径传给 `images` / `image` / `image_path`，否则会 `realpath` ENOENT。默认用 data URI。

仅当满足其一才可传本地路径：

1. MCP 进程与附件在同一台机器；或
2. 该 Harness **本机**已部署类似 `codex-image-bridge`（路径 → data URI）并把 profile 指到桥。

腾讯云这台 DSH 的 `127.0.0.1:3093` 桥 **只服务本机**；新 Windows / 新云机 / 新 profile **不会自动带上**，接入时要单独说明或再架桥。

## 卸载

删除所安装的 Skill 文件夹；从客户端活动配置删除对应的单个 MCP 条目，再刷新。保留其他 MCP 服务和配置。使用前备份用于恢复，不删除整个配置文件。
