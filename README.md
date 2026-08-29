# 写作工坊 / writing-craft

一个跨 Agent 的中文写作 Skill：帮助用户构思、起草、改写、润色和审稿，同时保留真实作者声音、资料边界与情绪的复杂性。

完整项目位于 [writing-craft/](writing-craft/)。

## 包含内容

- 自适应写作访谈：短任务直接完成，复杂任务先判断场景、材料和修订范围。
- 资料核验：不把附件文件名、不可访问路径或局部节选伪装成已读全文。
- 作者声音、去 AI 味、事实账本和复杂情绪控制。
- 7 个 Before / After 改写案例，涵盖 AI 味、用户声音、无力感、功能性邮件、附件缺失与资料截断。
- Codex、Claude Code、Cursor、GitHub Copilot、Gemini CLI 的路由文件。
- 无第三方依赖的 `skill_doctor.py`，用于检查、恢复和同步镜像。

## 快速开始

```text
git clone https://github.com/zhangjiaqi-wed/write-writing.git
cd write-writing/writing-craft
python scripts/skill_doctor.py --check
```

权威入口：

```text
.agents/skills/writing-craft/SKILL.md
```

已加载本地技能的平台可使用 `$writing-craft`（Codex）或 `/writing-craft`（Claude Code）。其他环境可直接读取 `SKILL.md`。

详细说明、安装方式、恢复策略和示例见 [writing-craft/README.md](writing-craft/README.md)。

## 验证

```text
cd writing-craft
python -m unittest discover -s tests -v
python scripts/skill_doctor.py --check
```

## 许可

[Apache License 2.0](LICENSE)
