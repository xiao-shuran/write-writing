#!/usr/bin/env python3
"""Run lightweight, explainable editorial checks on a UTF-8 text file.

This is a diagnostic aid, not an authorship or AI detector. It reports signals
that can make prose feel flat or templated and leaves the editorial decision to
the writer or agent.
"""

from __future__ import print_function

import argparse
import json
import re
import sys
from pathlib import Path


GENERIC_OPENERS = (
    "在当今",
    "随着",
    "在这个快速发展的时代",
    "众所周知",
    "不可否认",
    "近年来",
)
GENERIC_CLOSERS = (
    "总的来说",
    "综上所述",
    "让我们共同",
    "相信未来",
    "希望这篇文章",
    "相信你看完",
)
ABSTRACT_WORDS = (
    "重要",
    "必要",
    "复杂",
    "多元",
    "深刻",
    "温暖",
    "治愈",
    "赋能",
    "提升",
    "促进",
    "推动",
    "实现",
    "值得思考",
    "美好",
    "积极",
)
TRANSITION_WORDS = (
    "但是",
    "然而",
    "可是",
    "却",
    "反而",
    "直到",
    "原来",
    "后来",
    "因此",
    "于是",
    "没想到",
)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？；?!])")
PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n")
MARKDOWN_PREFIX_RE = re.compile(r"^\s*(?:#{1,6}\s+|[-*+]\s+|\d+[.)]\s+|>\s+)")


def is_markdown_structure(sentence):
    """Avoid treating headings and list labels as prose rhythm signals."""
    stripped = sentence.strip()
    return (
        stripped.startswith("```")
        or stripped.startswith("~~~")
        or bool(MARKDOWN_PREFIX_RE.match(stripped))
        or (stripped.startswith("**") and stripped.endswith("**"))
    )


def emit(text, stream=None):
    """Write UTF-8 consistently even on a legacy Windows console locale."""
    stream = stream or sys.stdout
    payload = text if isinstance(text, bytes) else str(text).encode("utf-8")
    buffer = getattr(stream, "buffer", None)
    if buffer is not None:
        buffer.write(payload)
        buffer.write(b"\n")
        buffer.flush()
    else:
        stream.write(payload.decode("utf-8") + "\n")


def read_text(path):
    return path.read_text(encoding="utf-8-sig")


def split_paragraphs(text):
    return [part.strip() for part in PARAGRAPH_SPLIT_RE.split(text) if part.strip()]


def split_sentences(paragraph):
    parts = [part.strip() for part in SENTENCE_SPLIT_RE.split(paragraph) if part.strip()]
    return parts or [paragraph.strip()]


def first_line(text):
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def last_line(text):
    for line in reversed(text.splitlines()):
        line = line.strip()
        if line:
            return line
    return ""


def line_number(text, fragment):
    index = text.find(fragment)
    if index < 0:
        return None
    return text.count("\n", 0, index) + 1


def sentence_lengths(paragraphs):
    return [len(sentence) for paragraph in paragraphs for sentence in split_sentences(paragraph)]


def repeated_sentence_starts(paragraphs):
    starts = {}
    for paragraph in paragraphs:
        for sentence in split_sentences(paragraph):
            if is_markdown_structure(sentence):
                continue
            normalized = re.sub(r"[\s，。！？；：、,.!?;:]+", "", sentence)
            if len(normalized) >= 4:
                key = normalized[:4]
                starts.setdefault(key, []).append(sentence[:18])
    return {key: values for key, values in starts.items() if len(values) >= 3}


def audit_text(text, path="<text>"):
    paragraphs = split_paragraphs(text)
    sentences = [sentence for paragraph in paragraphs for sentence in split_sentences(paragraph)]
    non_space_length = len(re.sub(r"\s+", "", text))
    abstract_hits = []
    for word in ABSTRACT_WORDS:
        count = text.count(word)
        if count >= 2:
            abstract_hits.append({"word": word, "count": count})

    findings = []
    opener = first_line(text)
    if opener and any(opener.startswith(item) for item in GENERIC_OPENERS):
        findings.append(
            {
                "severity": "medium",
                "code": "generic-opening",
                "line": line_number(text, opener),
                "message": "开头使用了常见泛化引入，可能延迟真实问题或场景的出现。",
                "suggestion": "尝试从具体动作、异常结果、人物选择或读者真正的问题进入。",
            }
        )

    closer = last_line(text)
    if closer and any(item in closer for item in GENERIC_CLOSERS):
        findings.append(
            {
                "severity": "medium",
                "code": "generic-closing",
                "line": line_number(text, closer),
                "message": "结尾可能使用了通用收束语，未必给读者新的理解或选择。",
                "suggestion": "回到一个具体细节、边界判断、行动或仍未解决的余波。",
            }
        )

    if abstract_hits and non_space_length >= 160:
        findings.append(
            {
                "severity": "medium",
                "code": "abstract-density",
                "line": None,
                "message": "抽象评价词重复出现，具体事实或动作可能不够。",
                "suggestion": "逐项检查这些词后面是否有谁、何时、做了什么、付出什么代价或产生什么结果。",
                "details": abstract_hits,
            }
        )

    transition_count = sum(text.count(word) for word in TRANSITION_WORDS)
    if len(paragraphs) >= 4 and transition_count == 0:
        findings.append(
            {
                "severity": "low",
                "code": "no-visible-turn",
                "line": None,
                "message": "较长文本没有检测到明显的转折或认知变化信号；可能需要人工确认段落是否一路平滑。",
                "suggestion": "不必强行加转折词，先检查是否存在真实的反差、限制、反例、选择或视角变化。",
            }
        )

    starts = repeated_sentence_starts(paragraphs)
    if starts:
        findings.append(
            {
                "severity": "low",
                "code": "repeated-sentence-start",
                "line": None,
                "message": "多个句子共享相同开头，节奏可能显得机械。",
                "suggestion": "合并重复判断，或改变其中一两句的进入方式；不要为了打散而随机换词。",
                "details": starts,
            }
        )

    lengths = sentence_lengths(paragraphs)
    if len(lengths) >= 6:
        average = sum(lengths) / float(len(lengths))
        variance = sum((length - average) ** 2 for length in lengths) / float(len(lengths))
        if variance < 20 and average >= 10:
            findings.append(
                {
                    "severity": "low",
                    "code": "uniform-rhythm",
                    "line": None,
                    "message": "句长过于接近，文章可能缺少快慢和停顿变化。",
                    "suggestion": "让行动句更利落、解释句更完整，并在关键判断前后留出空间。",
                    "details": {"sentence_count": len(lengths), "average_length": round(average, 1)},
                }
            )

    short_text_note = None
    if non_space_length < 120:
        short_text_note = "文本较短，统计信号仅供参考；优先检查是否完成了场景目的。"

    signal_count = len(findings)
    if signal_count == 0:
        verdict = "未发现明显模板化/平淡信号；这不是质量证明，仍需结合读者和材料人工判断。"
    elif any(item["severity"] == "medium" for item in findings):
        verdict = "建议先做结构或材料组织检查，再进行逐句润色。"
    else:
        verdict = "有轻量节奏信号，先人工确认是否真的影响阅读，再决定是否改写。"

    return {
        "path": str(path),
        "paragraph_count": len(paragraphs),
        "sentence_count": len(sentences),
        "character_count": non_space_length,
        "finding_count": signal_count,
        "verdict": verdict,
        "note": short_text_note,
        "findings": findings,
    }


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 text or Markdown file to audit.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser.parse_args()


def main():
    args = parse_args()
    path = Path(args.input)
    try:
        result = audit_text(read_text(path), path)
    except (OSError, UnicodeError) as error:
        emit("无法读取输入文件：%s" % error, sys.stderr)
        return 2

    if args.json:
        emit(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    emit("文本体检：%s" % result["path"])
    emit("段落 %d，句子 %d，字符 %d" % (
        result["paragraph_count"],
        result["sentence_count"],
        result["character_count"],
    ))
    emit("判断：%s" % result["verdict"])
    if result["note"]:
        emit("说明：%s" % result["note"])
    for finding in result["findings"]:
        location = "第 %s 行" % finding["line"] if finding["line"] else "全文"
        emit("[%s] %s（%s）" % (finding["severity"], location, finding["code"]))
        emit("  %s" % finding["message"])
        emit("  建议：%s" % finding["suggestion"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
