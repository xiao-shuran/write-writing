---
name: writing-craft-setup
description: Portable setup guide for the writing-craft Chinese writing skill.
---

# 写作工坊跨平台使用说明

这是一个可移植的中文写作 Skill 包。它的完整工作流、references、恢复工具和跨 Agent 入口都在同一个目录中。保留目录结构，不要只拷贝一份 `SKILL.md` 后期待所有辅助能力仍然可用。

## 推荐目录结构

要让各 Agent 自动发现入口文件，推荐将 `writing-craft/` 本身作为项目根目录打开，或将包内的入口目录和规则**合并**到既有项目根目录。仅把整个包放在其他项目的子目录中，通常仍可由 Agent 显式读取 `SKILL.md`，但 `AGENTS.md`、`CLAUDE.md` 和类似根级入口未必会被宿主项目自动发现。

完整包结构如下：

```text
writing-craft/
├── .agents/skills/writing-craft/    # 权威 Skill 副本
├── .claude/skills/writing-craft/    # Claude 兼容镜像
├── AGENTS.md                        # 通用 Agent / Codex 路由
├── CLAUDE.md                        # Claude Code 路由
├── GEMINI.md                        # Gemini CLI 路由
├── .github/copilot-instructions.md  # Copilot 路由
├── .cursor/rules/writing-craft.mdc  # Cursor 路由
├── references/                      # 根目录镜像，供直接读取时降级
├── scripts/skill_doctor.py          # 无第三方依赖的检查与恢复工具
└── MANIFEST.json                    # 包完整性清单
```

不同 Agent 对目录发现的支持不完全相同，因此入口文件只负责把 Agent 路由到同一个权威文件：

`.agents/skills/writing-craft/SKILL.md`

若此路径不可用，入口依次回退到根目录 `SKILL.md` 和 `.claude/skills/writing-craft/SKILL.md`。

也可以把 `.agents/skills/writing-craft/` 整个目录单独安装到某个 Agent 的本地技能目录。单独安装时它作为独立 skill 正常工作，但不具备跨平台镜像恢复能力；恢复工具会把它识别为独立安装，不会在宿主项目中擅自创建入口文件。保留完整 `writing-craft/` 包才能使用平台入口和镜像恢复。

## 平台使用

| 环境 | 首选方式 | 找不到 Skill 时 |
|---|---|---|
| Codex | 在加载该项目 Skill 的新会话中使用 `$writing-craft`，或直接提出中文写作任务 | 让 Agent 直接读取 `.agents/skills/writing-craft/SKILL.md`。 |
| Claude Code | 在已加载技能目录的新会话中使用 `/writing-craft` | 读取 `.agents/skills/writing-craft/SKILL.md` 或 `.claude/skills/writing-craft/SKILL.md`。 |
| Cursor | 由 `.cursor/rules/writing-craft.mdc` 路由 | 在项目规则或对话中显式指定权威 `SKILL.md` 路径。 |
| GitHub Copilot | 由 `.github/copilot-instructions.md` 路由 | 在仓库指令中加入权威 `SKILL.md` 路径。 |
| Gemini CLI / 其他 Markdown Agent | 由 `GEMINI.md` 或 `AGENTS.md` 路由 | 直接把 `SKILL.md` 与需要的 `references/` 作为上下文。 |

平台通常会在会话启动时发现本地技能。复制、恢复或切换分支后，重开当前项目根目录下的 Agent 会话再调用。没有任何平台入口可用时，技能仍可通过直接读取 `SKILL.md` 使用。

## 集成到已有项目

已有项目中若已存在 `AGENTS.md`、`CLAUDE.md`、`GEMINI.md`、`.claude/settings.json` 或 Copilot 指令文件，不要用本包的同名文件直接覆盖它们。保留原有内容，并合并以下最小路由：

```text
当用户请求中文写作、改写、润色、构思或审稿时，读取 .agents/skills/writing-craft/SKILL.md。
若该路径不可用，回退到 writing-craft/SKILL.md 或 .claude/skills/writing-craft/SKILL.md，
并遵循其资料核验、事实边界、作者声音、修订范围和文件缺失降级规则。
```

随后将 `.agents/skills/writing-craft/` 复制或注册到宿主项目支持的技能目录。Claude Code 的 `settings.json`、Cursor 规则和 Copilot 指令应与项目已有配置合并；本包的恢复脚本不会覆盖已有平台入口文件。

## 检查、恢复与同步

在 `writing-craft/` 根目录运行：

```text
python scripts/skill_doctor.py --check
python scripts/skill_doctor.py --repair
python scripts/skill_doctor.py --sync
python scripts/skill_doctor.py --repair --root <技能包根目录> --rebuild-distribution
```

- `--check`：报告缺失文件、镜像差异和缺失的平台入口。
- `--repair`：只补缺失文件，不覆盖内容不同的镜像或已有平台配置。
- `--sync`：用权威 `.agents/skills/writing-craft/` 副本刷新根目录和 Claude 镜像。只有确认权威副本是最新版本时才运行。
- `--rebuild-distribution`：仅当根标记、平台入口和镜像均已丢失时，显式从根目录残留文件重建完整跨平台包；必须与 `--root` 一起使用，不能用于独立安装的 skill 文件夹。

脚本只使用 Python 标准库，只在本技能目录内复制管理文件；不联网、不删除文件、不读取或修改用户稿件。

## 维护规则

1. 日常使用：从 `.agents/skills/writing-craft/SKILL.md` 开始。
2. 修改 Skill：编辑权威 `.agents/skills/writing-craft/` 中的文件，然后运行根目录 `scripts/skill_doctor.py --sync`。
3. 只丢失文件：运行 `--repair`，它不会覆盖内容已有差异的镜像。
4. 权威副本也丢失单个文件：`--repair` 会尝试从根目录或 Claude 镜像补回。
5. 完全无法恢复时：按 [references/fallbacks.md](references/fallbacks.md) 的最低可用流程继续写作，不从不明来源下载替代文件。

## 最低可用模式

即使 Python、镜像或某个 reference 缺失，只要能够读取任一 `SKILL.md`，仍可完成：确认需求与场景、核验用户资料是否可读、区分事实/推断/未知、选择构思或修订范围、交付文本并自检清晰度与事实边界。技能包缺失见 [references/fallbacks.md](references/fallbacks.md)，用户附件、路径或资料包缺失见 [references/input-materials.md](references/input-materials.md)。
