# writing-craft

For Chinese writing tasks, use `.agents/skills/writing-craft/SKILL.md` as the shared workflow. Fall back to the package-root `SKILL.md`, then `.claude/skills/writing-craft/SKILL.md` if needed.

Do not assume a full interview is needed for a small edit. Use the adaptive task gate, preserve confirmed facts and the user's own voice, and follow `references/fallbacks.md` when a skill file is missing. Claude Code may invoke this skill as `/writing-craft` when the platform has loaded the registered path.
