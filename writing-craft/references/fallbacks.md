# 文件缺失与环境降级

这个技能包应当在 Codex、Claude Code、Cursor、Copilot、Gemini CLI 和其他能读取 Markdown 指令的 Agent 环境中保持可用。不同平台的发现方式不同，文件、脚本或配置也可能在复制时遗漏。缺失时先恢复可验证的本地副本；恢复不了时使用最低可用流程继续帮助用户，不把缺失内容假装成已读取。

## 最低可用写作流程

只要当前还能读到任一 `SKILL.md`，就可以继续：

1. 从当前对话确认或推断用户的需求和使用场景；缺失且会改变文本时，问最少的问题。
2. 判断任务是快速、标准还是深度，并说明必要假设。
3. 区分已知事实、推断和未知内容；不编造。
4. 根据用户要求写、改、润色或审稿。
5. 自检清晰度、场景适配、事实边界和修订范围。

任何可选 reference 缺失都不能阻止这五步。

## 用户提供资料缺失或不可用

用户资料的缺失与技能包文件缺失不同：它会直接限制哪些事实、引语、声音和结论可以使用。用户提到附件、路径、链接、样稿、截图、媒体或资料包时，读取 [input-materials.md](input-materials.md)。

最低规则是：不能读取就明确说明；文件名和摘要不算证据；关键资料缺失时给框架、条件化版本或只补问一项决定性资料；非关键资料缺失时说明未使用并继续；绝不把未读资料伪装成已读。

## 缺失矩阵

| 缺失内容 | 立即动作 | 降级方式 | 恢复方式 |
|---|---|---|---|
| `MANIFEST.json` | 不信任目录是否完整 | 使用当前 `SKILL.md` 的最低可用流程 | 运行 `scripts/skill_doctor.py --repair`；脚本内置必要文件列表。 |
| 当前 `SKILL.md` | 查找 `.agents/skills/writing-craft/SKILL.md`、根目录 `SKILL.md`、`.claude/skills/writing-craft/SKILL.md` | 使用找到的副本；若都没有，按最低可用写作流程工作 | 从任一完整本地副本复制，或运行本地 `skill_doctor.py --repair`。 |
| 单个 `references/*.md` | 只处理该 reference 的能力缺口 | 使用本文件中的基础规则；不要虚构缺失 reference 的内容 | 从本地镜像恢复；脚本会校验并同步核心参考文件。 |
| `voice-profile.md` | 不建立长期声音画像 | 保守修订，保留用户原句和明确要求 | 继续前可请用户提供一两段样稿；恢复文件后再做画像。 |
| `material-ledger.md` | 提高事实审慎度 | 不编造，事实与推断分开，不确定则条件化，引语须可核验 | 恢复后再处理复杂人物、数据或引用任务。 |
| 情绪或文学 reference | 不套文学参照 | 用用户提供的事实、动作、限度和结尾目标控制情绪 | 恢复后才使用特定情绪模型或文学组织方式。 |
| `scripts/skill_doctor.py` 或 Python 不可用 | 不运行恢复命令 | 手动比较本地镜像的文件名与内容，不删除任何文件 | 从完整镜像复制脚本，或只继续最低可用流程。 |
| 平台入口文件 | 不假定该平台会自动发现 skill | 直接要求 Agent 读取可见的 `SKILL.md` 路径 | 执行 `skill_doctor.py --repair` 重建入口；重启平台会话以重新加载。 |
| 所有本地副本均缺失 | 说明无法恢复原技能内容 | 用最低可用写作流程处理当前任务，不声称在用该 skill | 从可信备份或原始发布包恢复；不要从不明来源下载替代文件。 |

## 恢复命令

优先从技能包根目录运行：

```text
python scripts/skill_doctor.py --check
python scripts/skill_doctor.py --repair
```

若某个平台使用不同的 Python 命令，可使用该环境的 Python 解释器。脚本不依赖第三方包，不联网，不删除文件，不读取或写入用户稿件；它只检查并在本技能目录内恢复镜像与平台入口。

`--check` 返回非零表示包不完整或镜像不一致。先看报告：文件缺失时运行 `--repair`，镜像内容不一致但确认应以权威副本为准时运行 `--sync`。若根标记、平台入口和镜像目录都丢失，只剩根目录 skill 文件时，显式运行 `python scripts/skill_doctor.py --repair --root <技能包根目录> --rebuild-distribution`；该参数会重建跨平台结构，因此不能用于独立安装的 skill 文件夹。恢复后在当前目录重开 Agent 会话，保证平台重新发现本地 skill。

## 手动恢复原则

- 完整包中 `.agents/skills/writing-craft/` 是权威副本；根目录和 `.claude/skills/writing-craft/` 是镜像。权威副本缺失单个文件时，才从镜像中补回。
- `--repair` 只补缺失，不覆盖内容不同的镜像；确认以权威副本为准后，才显式使用 `--sync`。无法确定最新版本时，不要静默覆盖。
- 只有一个单独安装的 `.agents/skills/writing-craft/` 文件夹时，它是独立 skill，不应被当作损坏的完整分发包；不要据此在宿主项目中创建根目录入口或覆盖项目配置。
- 仅复制技能自身文件。不要覆盖用户文章、项目配置或其他 Agent 的无关规则。
- 恢复后比较 `SKILL.md`、`MANIFEST.json`、`agents/openai.yaml`、`references/` 和 `scripts/skill_doctor.py` 是否一起存在。

## 平台发现回退

各平台的自动发现策略不同。自动发现失败时，通用回退是从项目根目录直接读取下列优先路径之一：

1. `.agents/skills/writing-craft/SKILL.md`
2. `SKILL.md`
3. `.claude/skills/writing-craft/SKILL.md`

`AGENTS.md`、`CLAUDE.md`、`GEMINI.md`、`.github/copilot-instructions.md` 和 `.cursor/rules/writing-craft.mdc` 都应指向第一个路径，并在它缺失时指向根目录副本。它们是入口提示，不含业务写作规则的完整副本，避免不同平台的规则逐渐漂移。

技能包若作为其他项目的子目录存在，这些入口提示未必会被宿主项目发现。此时应让 Agent 显式读取包内 `SKILL.md`，或把最小路由合并到宿主项目已有的入口文件。不要以“恢复平台入口”为由覆盖宿主项目现有规则或配置。
