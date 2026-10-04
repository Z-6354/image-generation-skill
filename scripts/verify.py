"""Offline package checks. No network, image generation or third-party libraries."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    'SKILL.md', 'README.md', 'LICENSE', '.gitignore',
    'references/setup.md', 'references/mcp.md',
    'mcp/mcp.example.json', 'mcp/dsh.cordis.patch.example.yml',
    'scripts/verify.py',
}


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def verify():
    actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*')
              if p.is_file() and '.git' not in p.relative_to(ROOT).parts
              and '__pycache__' not in p.relative_to(ROOT).parts
              and 'dist' not in p.relative_to(ROOT).parts}
    check(actual == EXPECTED, f'Unexpected/missing package files: {sorted(actual ^ EXPECTED)}')
    skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
    front = re.match(r'^---\n(.*?)\n---\n', skill, re.S)
    check(front is not None, 'Skill frontmatter missing')
    check('name: codex-image' in front[1], 'Skill name mismatch')
    check('description: ' in front[1], 'Skill description missing')
    check('on first use' in front[1].lower(), 'First-use trigger missing')

    for relative in sorted(EXPECTED):
        path = ROOT / relative
        text = path.read_text(encoding='utf-8')
        # Error messages never include matched secrets.
        check(not re.search(r'(?:sk-[A-Za-z0-9]{16,}|gh[pousr]_[A-Za-z0-9]{20,})', text),
              f'Possible credential in {relative}')
        if relative != 'scripts/verify.py':
            tokens = re.findall(r'Bearer\s+([^\s"\'`<>]+)', text)
            check(all(t == 'REPLACE_WITH_YOUR_TOKEN' for t in tokens),
                  f'Non-placeholder bearer token in {relative}')
        check('C:\\Users\\han' not in text and 'D:\\0HAN' not in text,
              f'Author machine path in {relative}')
        if path.suffix == '.md':
            prose = re.sub(r'```.*?```', '', text, flags=re.S)
            prose = re.sub(r'`[^`\n]*`', '', prose)
            for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', prose):
                target = target.strip('<>')
                if '://' in target or target.startswith('#'):
                    continue
                target = target.split('#', 1)[0]
                check((path.parent / target).is_file(), f'Broken link in {relative}: {target}')

    config = json.loads((ROOT / 'mcp/mcp.example.json').read_text(encoding='utf-8'))
    server = config['mcpServers']['codex-image']
    check(server['url'] == 'https://vps.wannian.fun/codex-image-mcp/mcp', 'Wrong endpoint')
    check(server['headers'] == {'Authorization': 'Bearer REPLACE_WITH_YOUR_TOKEN'},
          'Example credentials must be placeholders')
    yaml = (ROOT / 'mcp/dsh.cordis.patch.example.yml').read_text(encoding='utf-8')
    for field in ['- insert:', 'serverName: codex-image', 'transport: streamable-http',
                  'toolCallTimeoutMs: 180000', '@deepseek-ai/dsh-mcp-client', server['url']]:
        check(field in yaml, f'DSH template missing {field}')
    for policy in ['直接调用', '不要重装', '当前工具 schema', 'SHA-256', '内联预览',
                   '不主动生成付费测试图片', '超时不代表服务端未执行', '只看图']:
        check(policy in skill, f'Workflow constraint missing: {policy}')
    print(f'PASS: {len(EXPECTED)} files; frontmatter, links, templates, '
          'credential scan and first-use/reuse/delivery rules verified offline.')


if __name__ == '__main__':
    verify()
