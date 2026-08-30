# 写作工坊 / writing-craft

一个可移植的中文写作 Agent Skill，用于构思、起草、改写、润色和审稿。它面向真正的写作任务：既要让文字清楚、自然、有作者感，也要在资料不完整、场景复杂或情绪较重时守住事实边界。

它不是“把所有文本写得更华丽”的提示词集合。它会先判断任务和使用场景，再决定该直接改、补问一个关键问题，还是建立材料账本和写作策略。

## 能做什么

- 为文章、邮件、口播、演讲、社交内容、叙事和人物稿建立结构或初稿。
- 以保守、结构或探索三种范围改写已有文本，避免“润色”变成擅自重写。
- 降低模板感和 AI 味，保留用户原本的判断、节奏、犹豫和细节，而不伪造个人经历。
- 检查用户资料是否实际可读、是否截断、版本是否冲突，以及资料缺失会怎样影响成稿。
- 区分确认事实、合理推断、待补材料和明确许可的虚构内容。
- 用“主情绪、伴随情绪、触发事实、行动冲动、现实限度和余波”组织情绪写作，不把无力感自动改成励志或释怀。
- 从中国文学与历史文本中提取高层的情绪组织方式，不复制在世作者或其他作者的可识别表达。
- 提供可对照的 Before / After 改写示例，而不只给抽象规则。
- 通过“阅读动能”检查文章是否有问题、阻力、变化、节奏和结尾回报，避免正确但无聊。
- 提供“克制观察、稳定张力、强烈推进、轻巧机锋、沉浸叙事”五种阅读体验档位，避免所有文章都写成同一种温吞语气。
- 提供 `prose_audit.py` 文本体检工具，提示常见模板和节奏信号；它不是 AI 检测器或文学评分器。
- 提供专业文体档位、去空白字符计数、严格上限检查，以及按需保存和比较稿件版本。
- 在 Codex、Claude Code、Cursor、GitHub Copilot、Gemini CLI 等环境中使用；文件缺失时可检查、修复或降级继续工作。

## 快速开始

克隆仓库后，进入 skill 目录：

```text
git clone https://github.com/xiao-shuran/write-writing.git
cd write-writing/writing-craft
```

完整包的权威入口是：

```text
.agents/skills/writing-craft/SKILL.md
```

已发现本地技能的平台通常可以这样调用：

```text
# Codex
$writing-craft

# Claude Code
/writing-craft
```

如果平台没有自动发现 skill，直接让 Agent 读取 `SKILL.md` 或 `.agents/skills/writing-craft/SKILL.md` 即可。复制、恢复或切换分支后，建议从项目根目录重开 Agent 会话。

更完整的跨平台安装与维护说明见 [GUIDE.md](GUIDE.md)。

首次使用可直接按 [快速上手](references/quickstart.md) 中的五种请求开始，不必先填写完整 brief。

## 它如何判断任务

写作工坊不会每次都弹出一张问卷。它先按任务风险和复杂度分流：

| 类型 | 例子 | 默认动作 |
|---|---|---|
| 快速任务 | 改标题、改一句话、短消息、纠错 | 在同一轮给简短判断和结果；只在场景会改变措辞时补问一个问题。 |
| 标准任务 | 邮件、帖子、短文、已有稿件的改写或审稿 | 补齐任务、场景和目标中的关键缺项，再给简短写作判断。 |
| 深度任务 | 长文、演讲、人物稿、情绪写作、含数据或敏感材料的文本 | 先确认使用场景、材料边界和修订范围；默认等待确认后再写。 |

深度任务的判断会明确：交付形式、读者与场景、核心策略、阅读体验档位、材料边界和修订范围。用户明确说“直接写”时，skill 会列出必要假设后继续，但不会把假设写成事实。

如果是专业场景，可选择执行摘要、决策备忘录、项目复盘、研究报告、提案、客户沟通或公开说明等文体。详见 [professional-styles.md](references/professional-styles.md)。

## 用户资料不是“默认已读”

当用户提到附件、路径、链接、样稿、采访、截图、音视频、表格或“按资料写”时，skill 会先核验资料状态：

- 是否存在且可读。
- 是否只读到一部分，或内容被截断。
- 是否存在版本冲突、时间线冲突或缺少说话者/引用上下文。
- 它是关键资料还是非关键资料。

关键资料不可读时，skill 不会假装已经看过文件，也不会补造引语、经历、数字或人物动机。它会请求一项决定性资料，或先给结构稿、条件化版本、待填位置或不依赖该资料的通用版本。

详细规则见 [references/input-materials.md](references/input-materials.md) 与 [references/material-ledger.md](references/material-ledger.md)。

## Before / After 示例

下面是一个缩略示例。完整的 7 个改写场景，以及专门处理“文章太平”的四组对照，见 [references/rewrite-examples.md](references/rewrite-examples.md) 和 [references/reader-momentum.md](references/reader-momentum.md)。

**Before**

> 在当今快节奏的工作环境中，高效沟通显得尤为重要。团队应该建立更加完善的协作机制，提高信息传递效率，及时发现和解决潜在问题。

**已知材料**

项目经理每周五需向 6 位成员逐个收集进度，约耗时 3 小时；周报没有风险字段；负责人常到周一才知道项目卡住。

**After**

> 每周五，项目经理要逐个问 6 个人进度，3 小时过去，周报才凑齐。但周报里没有风险栏，负责人往往到周一才知道项目已经卡住。问题不在大家不愿意汇报，而在这份报告只收集了“做了什么”，没有逼人回答“哪里可能出事”。

改写动作不是“多写点细节”这么简单，而是：只使用已知材料、用流程与后果替换空词、提出可讨论的判断，并避免补造责任归属或失败案例。

阅读动能也不是夸张：先让读者遇到一个具体问题或反常，再让事实、阻力和选择改变理解，最后给出新的认识或准确的未完成状态。

默认档位是“稳定张力”：文章要有清楚的问题、真实的阻力和一到两个转向，但不靠标题党、连续金句或虚构冲突吸引人。

## 人味与情绪的边界

“有人味”不等于故意写错、过度口语化、加入网络热词，或替用户虚构创伤和经历。它来自作者真实的观察位置、偏好、细节和限度。

情绪写作也不等于更大声。特别是在无力感、哀痛、羞耻、焦虑或复杂关系中，skill 会先回答：发生了什么、想要什么、什么阻挡了它、什么无法改变、还剩下什么行动，以及什么仍未解决。

相关参考：

- [去 AI 味与作者声音](references/human-voice.md)
- [作者声音画像](references/voice-profile.md)
- [情绪清晰度与无力感](references/emotional-clarity.md)
- [情绪地图与表达控制](references/emotion-atlas.md)
- [中国文学与历史文本的情绪组织参照](references/literary-reference.md)

## 目录结构

```text
writing-craft/
├── .agents/skills/writing-craft/    # 权威 skill 副本
├── .claude/skills/writing-craft/    # Claude 兼容镜像
├── AGENTS.md / CLAUDE.md / GEMINI.md
├── .cursor/ / .github/              # Cursor、Copilot 路由
├── SKILL.md                          # 根目录镜像与直接入口
├── references/
│   ├── rewrite-examples.md           # Before / After 示例库
│   ├── reader-momentum.md            # 张力、节奏和反平淡质量门
│   ├── length-control.md              # 字数和篇幅控制
│   ├── draft-versions.md              # 稿件快照、比较和恢复
│   ├── professional-styles.md         # 专业文体档位
│   ├── interaction-contract.md        # 统一交互形状
│   ├── quality-evaluation.md          # 深度质量评估
│   ├── input-materials.md            # 用户资料核验与缺失降级
│   ├── material-ledger.md            # 事实、推断和虚构边界
│   ├── voice-profile.md              # 用户声音画像
│   ├── human-voice.md                # 去模板感与人味
│   ├── emotion-atlas.md              # 情绪识别与控制
│   ├── emotional-clarity.md          # 无力感等复杂情绪
│   ├── literary-reference.md         # 文学参照
│   └── fallbacks.md                  # 文件/环境降级策略
├── scripts/skill_doctor.py           # 检查、修复和同步工具
├── scripts/prose_audit.py            # Markdown/TXT 成稿启发式体检
├── scripts/draft_versions.py         # 按需创建、比较和恢复本地稿件版本
└── tests/                            # 包契约与恢复测试
```

## 检查、恢复与同步

恢复工具只使用 Python 标准库，不联网、不删除文件、不读取或修改用户稿件。

```text
python scripts/skill_doctor.py --check
python scripts/skill_doctor.py --repair
python scripts/skill_doctor.py --sync
python scripts/prose_audit.py draft.md --target-chars 800
python scripts/draft_versions.py snapshot draft.md --store-dir draft_versions --label initial
```

- `--check` 报告缺失文件、镜像差异和缺失的平台入口。
- `--repair` 只补缺失文件，不覆盖内容不同的镜像或已有平台配置。
- `--sync` 用权威 `.agents/skills/writing-craft/` 副本刷新根目录和 Claude 镜像。

字数契约默认按去除空白后的字符数计数；严格上限优先于“字数左右”。稿件版本只在用户明确要求时保存，并且恢复总是输出到新文件，不覆盖原稿。

如果根标记、平台入口和镜像目录都丢失，但根目录副本仍在，可显式重建完整包：

```text
python scripts/skill_doctor.py --repair --root <技能包根目录> --rebuild-distribution
```

独立安装的 `.agents/skills/writing-craft/` 文件夹不会被误认为损坏的完整分发包，也不会在宿主项目中擅自创建配置文件。

## 验证

```text
python -m unittest discover -s tests -v
python scripts/skill_doctor.py --check
```

测试覆盖：跨 Agent 镜像一致性、入口与 reference 路由、缺失文件恢复、镜像漂移保护、独立 skill 安装、完整分发包重建、用户资料缺失处理和改写示例库。

## 许可

本仓库使用 [Apache License 2.0](../LICENSE)。
