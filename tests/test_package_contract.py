import json
import re
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_ROOT = PACKAGE_ROOT / ".agents" / "skills" / "writing-craft"
CLAUDE_ROOT = PACKAGE_ROOT / ".claude" / "skills" / "writing-craft"


class PackageContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((PACKAGE_ROOT / "MANIFEST.json").read_text(encoding="utf-8"))

    def test_manifest_has_expected_canonical_layout(self):
        self.assertEqual(self.manifest["name"], "writing-craft")
        self.assertEqual(self.manifest["canonical_path"], ".agents/skills/writing-craft")
        self.assertEqual(self.manifest["mirror_paths"], [".", ".claude/skills/writing-craft"])
        self.assertEqual(len(self.manifest["core_files"]), len(set(self.manifest["core_files"])))

    def test_managed_files_exist_and_match_all_mirrors(self):
        for relative in self.manifest["core_files"]:
            with self.subTest(relative=relative):
                root_file = PACKAGE_ROOT / relative
                canonical_file = CANONICAL_ROOT / relative
                claude_file = CLAUDE_ROOT / relative
                self.assertTrue(root_file.is_file(), msg=str(root_file))
                self.assertTrue(canonical_file.is_file(), msg=str(canonical_file))
                self.assertTrue(claude_file.is_file(), msg=str(claude_file))
                self.assertEqual(root_file.read_bytes(), canonical_file.read_bytes())
                self.assertEqual(canonical_file.read_bytes(), claude_file.read_bytes())

    def test_platform_entries_route_to_canonical_skill(self):
        for relative in self.manifest["platform_entries"]:
            with self.subTest(relative=relative):
                path = PACKAGE_ROOT / relative
                self.assertTrue(path.is_file(), msg=str(path))
                self.assertIn(
                    ".agents/skills/writing-craft",
                    path.read_text(encoding="utf-8"),
                )

    def test_skill_frontmatter_and_routed_references_are_valid(self):
        skill = (PACKAGE_ROOT / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"^---\n(?P<frontmatter>.*?)\n---\n", skill, re.DOTALL)
        self.assertIsNotNone(match)
        self.assertRegex(match.group("frontmatter"), r"(?m)^name:\s*writing-craft$")
        self.assertRegex(match.group("frontmatter"), r"(?m)^description:")

        routes = re.findall(r"\]\(references/([a-z0-9-]+\.md)\)", skill)
        self.assertGreaterEqual(len(routes), 8)
        for reference in routes:
            with self.subTest(reference=reference):
                self.assertTrue((PACKAGE_ROOT / "references" / reference).is_file())

    def test_skill_uses_adaptive_intake_and_fallback_rules(self):
        skill = (PACKAGE_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("快速", skill)
        self.assertIn("标准", skill)
        self.assertIn("深度", skill)
        self.assertIn("快速任务不需要额外等待", skill)
        self.assertIn("材料账本", skill)
        self.assertIn("修订范围", skill)
        self.assertIn("最低可用流程", skill)

    def test_skill_routes_and_enforces_user_material_handling(self):
        skill = (PACKAGE_ROOT / "SKILL.md").read_text(encoding="utf-8")
        materials = (PACKAGE_ROOT / "references" / "input-materials.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("references/input-materials.md", skill)
        self.assertIn("资料缺失", skill)
        self.assertIn("未找到", materials)
        self.assertIn("版本冲突", materials)
        self.assertIn("截断", materials)
        self.assertIn("关键资料", materials)
        self.assertIn("绝不", materials)

    def test_rewrite_examples_are_routed_and_include_actionable_contrasts(self):
        skill = (PACKAGE_ROOT / "SKILL.md").read_text(encoding="utf-8")
        examples = (PACKAGE_ROOT / "references" / "rewrite-examples.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("references/rewrite-examples.md", skill)
        self.assertGreaterEqual(examples.count("**Before"), 7)
        self.assertGreaterEqual(examples.count("**After"), 7)
        self.assertGreaterEqual(examples.count("**已知材料**"), 7)
        self.assertIn("不能做什么", examples)
        self.assertIn("附件无法读取", examples)
        self.assertIn("无力感", examples)

    def test_readme_introduces_core_workflows_and_links(self):
        readme = (PACKAGE_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("写作工坊 / writing-craft", readme)
        self.assertIn("Before / After", readme)
        self.assertIn("references/rewrite-examples.md", readme)
        self.assertIn("references/input-materials.md", readme)
        self.assertIn("scripts/skill_doctor.py --check", readme)
        self.assertIn("Apache License 2.0", readme)

    def test_reader_momentum_reference_is_routed_and_actionable(self):
        skill = (PACKAGE_ROOT / "SKILL.md").read_text(encoding="utf-8")
        momentum = (PACKAGE_ROOT / "references" / "reader-momentum.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("references/reader-momentum.md", skill)
        self.assertIn("阅读动能", momentum)
        self.assertIn("反平淡修订流程", momentum)
        self.assertIn("质量门：交付前快速评分", momentum)
        self.assertIn("不要用这些方式制造", momentum)
        self.assertGreaterEqual(momentum.count("Before"), 4)
        self.assertGreaterEqual(momentum.count("After"), 4)
        self.assertIn("已知材料", momentum)
        self.assertIn("平静不是平淡", momentum)
        self.assertIn("阅读契约", momentum)
        self.assertIn("三遍起草", momentum)
        self.assertIn("段落审计", momentum)
        self.assertIn("漂亮但平", momentum)

    def test_prose_audit_tool_is_packaged_and_documented(self):
        skill = (PACKAGE_ROOT / "SKILL.md").read_text(encoding="utf-8")
        readme = (PACKAGE_ROOT / "README.md").read_text(encoding="utf-8")
        guide = (PACKAGE_ROOT / "GUIDE.md").read_text(encoding="utf-8")
        audit = PACKAGE_ROOT / "scripts" / "prose_audit.py"
        self.assertTrue(audit.is_file())
        self.assertIn("prose_audit.py", skill)
        self.assertIn("prose_audit.py", readme)
        self.assertIn("prose_audit.py", guide)
        self.assertIn("AI detector", audit.read_text(encoding="utf-8"))

    def test_no_obsolete_emotion_reference_remains(self):
        self.assertFalse((PACKAGE_ROOT / "references" / "chinese-emotional-voices.md").exists())


if __name__ == "__main__":
    unittest.main()
