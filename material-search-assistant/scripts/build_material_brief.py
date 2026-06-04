#!/usr/bin/env python3
"""Generate a starter material brief from a script text file."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DEFAULT_SPEC = {
    "target_platforms": ["weibo", "xiaohongshu", "bilibili", "news", "official_sites", "github"],
    "material_types": ["screenshot", "image", "video"],
    "must_show": ["core idea of the segment"],
    "disallowed_noise": ["heavy ads", "blocking overlays", "blur", "weak title-only match"],
    "suggested_visual_style": "clean, legible, fast to understand",
}

REMOTION_STYLE_OPTIONS = [
    "苹果发布会极简（推荐）",
    "终端电影感",
    "编辑部信息图",
]

SHOT_TYPE_MAP = {
    "热度证明": "establishing_shot",
    "概念定义": "screen_focus",
    "能力演示": "screen_focus",
    "真实体验": "workspace_atmosphere",
    "风险提醒": "insert_shot",
    "技能生态": "tracking_shot",
    "结尾引导": "establishing_shot",
}


RULES = [
    {
        "label": "热度证明",
        "keywords": ["热搜", "爆火", "全网", "刷屏", "火", "hot search", "viral", "trending"],
        "communication_goal": "prove broad public attention",
        "material_types": ["screenshot", "news screenshot", "social screenshot"],
        "target_platforms": ["weibo", "bilibili", "news"],
        "must_show": ["heat", "discussion density", "public attention"],
        "tone": "high-heat",
        "evidence_required": "yes",
    },
    {
        "label": "概念定义",
        "keywords": ["是什么", "叫", "定义", "意思", "what it is", "renamed", "icon"],
        "communication_goal": "explain what the thing is",
        "material_types": ["official screenshot", "product page", "image"],
        "target_platforms": ["official_sites", "docs", "news"],
        "must_show": ["definition", "product identity", "basic concept"],
        "tone": "clear",
        "evidence_required": "yes",
    },
    {
        "label": "能力演示",
        "keywords": ["可以", "帮你", "操控", "发邮件", "整理文件", "浏览器", "功能", "skill", "workflow", "demo"],
        "communication_goal": "show what it can do",
        "material_types": ["video", "screen recording", "ui screenshot"],
        "target_platforms": ["bilibili", "official_sites", "youtube"],
        "must_show": ["actual workflow", "usable function", "interaction"],
        "tone": "demonstrative",
        "evidence_required": "yes",
    },
    {
        "label": "真实体验",
        "keywords": ["我", "用了", "体验", "震撼", "提醒我", "bug", "卡住", "心累", "真实"],
        "communication_goal": "show lived usage and friction",
        "material_types": ["creator video", "community screenshot", "reaction screenshot"],
        "target_platforms": ["bilibili", "weibo", "xiaohongshu", "reddit"],
        "must_show": ["real usage", "first-person feel", "imperfection"],
        "tone": "personal",
        "evidence_required": "no",
    },
    {
        "label": "风险提醒",
        "keywords": ["风险", "删了", "安全", "问题", "危险", "焦虑", "限制", "warning", "risk"],
        "communication_goal": "show caution, limitations, or risk",
        "material_types": ["news screenshot", "official warning", "clean evidence screenshot"],
        "target_platforms": ["news", "official_sites", "github"],
        "must_show": ["risk", "limitation", "credible caution"],
        "tone": "calm",
        "evidence_required": "yes",
    },
    {
        "label": "技能生态",
        "keywords": ["skill", "工作流", "分享", "生态", "团队", "agent", "hub"],
        "communication_goal": "show ecosystem or packaging logic",
        "material_types": ["repo screenshot", "workflow screenshot", "multi-agent demo"],
        "target_platforms": ["github", "official_sites", "bilibili"],
        "must_show": ["ecosystem", "shareable workflow", "scale"],
        "tone": "systematic",
        "evidence_required": "yes",
    },
    {
        "label": "结尾引导",
        "keywords": ["推荐", "欢迎", "点赞", "评论", "收藏", "体验", "加入我的群", "cta"],
        "communication_goal": "support the closing call to action",
        "material_types": ["clean outro visual", "community screenshot", "logo or brand shot"],
        "target_platforms": ["official_sites", "stock", "community"],
        "must_show": ["invitation", "next step", "community or product entrance"],
        "tone": "inviting",
        "evidence_required": "no",
    },
]


def split_paragraphs(text: str) -> list[str]:
    chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n+", text) if chunk.strip()]
    if chunks:
        return chunks
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines


def score_rule(paragraph: str, rule: dict[str, object]) -> int:
    lower = paragraph.lower()
    score = 0
    for kw in rule["keywords"]:
        if str(kw).lower() in lower:
            score += 1
    return score


def choose_rule(paragraph: str, index: int, total: int) -> dict[str, object]:
    scored = [(score_rule(paragraph, rule), rule) for rule in RULES]
    scored.sort(key=lambda item: item[0], reverse=True)
    best_score, best_rule = scored[0]
    if best_score > 0:
        return best_rule
    if index == 0:
        return RULES[0]
    if index == total - 1:
        return RULES[-1]
    return RULES[min(index, len(RULES) - 2)]


def build_segment(paragraph: str, index: int, total: int) -> dict[str, object]:
    rule = choose_rule(paragraph, index, total)
    visual_mode = choose_visual_mode(paragraph, rule)
    segment = {
        "segment_id": f"{index + 1:02d}",
        "segment_label": rule["label"],
        "source_text": paragraph,
        "communication_goal": rule["communication_goal"],
        "material_types_needed": rule["material_types"],
        "emotional_tone": rule["tone"],
        "evidence_required": rule["evidence_required"],
        "visual_mode_candidate": visual_mode,
        "search_brief": {
            "target_platforms": rule["target_platforms"],
            "keywords": sorted({word for word in re.findall(r"[\w\u4e00-\u9fff]{2,20}", paragraph)})[:12],
            "must_show": rule["must_show"],
            "disallowed_noise": DEFAULT_SPEC["disallowed_noise"],
            "suggested_visual_style": DEFAULT_SPEC["suggested_visual_style"],
        },
    }
    if visual_mode in {"remotion_animation", "hybrid"}:
        segment["remotion_style_confirmation_required"] = True
        segment["remotion_style_options"] = REMOTION_STYLE_OPTIONS
        segment["remotion_brief_stub"] = build_remotion_stub(paragraph, rule, visual_mode)
    if visual_mode in {"shot_library", "hybrid", "video_prompt"}:
        shot_brief = build_shot_brief(paragraph, rule, visual_mode)
        segment["shot_brief_stub"] = shot_brief
        if shot_brief["generation_fallback"] == "video_prompt" or visual_mode == "video_prompt":
            segment["video_prompt_stub"] = build_video_prompt_stub(paragraph, shot_brief)
    return segment


def choose_visual_mode(paragraph: str, rule: dict[str, object]) -> str:
    lower = paragraph.lower()
    evidence_required = str(rule["evidence_required"]).lower() == "yes"
    normalized = paragraph.replace(" ", "").replace("\n", "")
    short_line = len(normalized) <= 40

    remotion_keywords = [
        "workflow",
        "step",
        "prompt",
        "animation",
        "motion",
        "terminal",
        "ui",
        "过程",
        "步骤",
        "动画",
        "演示",
        "界面",
        "终端",
        "输入",
        "输出",
        "为什么",
        "难道",
        "下一个",
        "原因",
        "第一次大规模地",
        "产品范式",
        "手和脚",
        "过渡形态",
        "飞入寻常百姓家",
    ]
    infographic_keywords = [
        "compare",
        "comparison",
        "framework",
        "summary",
        "diagram",
        "对比",
        "总结",
        "结构",
        "框架",
        "流程图",
    ]
    broll_keywords = [
        "atmosphere",
        "mood",
        "workspace",
        "office",
        "city",
        "氛围",
        "办公",
        "场景",
    ]
    shot_keywords = [
        "镜头",
        "空镜",
        "特写",
        "远景",
        "近景",
        "推进",
        "拉远",
        "运镜",
        "转场",
        "氛围镜头",
        "effect shot",
        "empty shot",
        "establishing shot",
        "close-up",
        "tracking shot",
        "camera move",
        "总的来说",
        "就在我们剪完片子的那一刻",
        "还要再等等看",
        "我们想",
        "未来",
        "彼岸",
        "风暴到来",
    ]

    remotion_score = sum(1 for kw in remotion_keywords if kw in lower)
    infographic_score = sum(1 for kw in infographic_keywords if kw in lower)
    broll_score = sum(1 for kw in broll_keywords if kw in lower)
    shot_score = sum(1 for kw in shot_keywords if kw in lower)

    # Title cards, chapter cards, and strong judgment lines should be animated.
    if short_line and ("？" in paragraph or "?" in paragraph):
        return "remotion_animation"
    if short_line and any(token in paragraph for token in ["四个原因", "第一", "第二", "第三", "第四"]):
        return "remotion_animation"
    if any(
        token in paragraph
        for token in [
            "不会像",
            "不会持续太久",
            "第一次大规模地",
            "给大模型装上了“手和脚”",
            "给大模型装上了“手和脚”".replace("“", '"').replace("”", '"'),
            "代表了一种新的产品范式",
            "过渡形态",
        ]
    ):
        return "remotion_animation"
    if any(
        token in paragraph
        for token in [
            "总的来说",
            "而就在我们剪完片子的那一刻",
            "我们想",
            "还要再等等看",
        ]
    ):
        return "shot_library"

    if evidence_required and remotion_score > 0:
        return "hybrid"
    if remotion_score >= 2:
        return "remotion_animation"
    if shot_score >= 2:
        return "shot_library"
    if infographic_score >= 2:
        return "infographic"
    if broll_score >= 1 and not evidence_required:
        return "stock_broll"
    return "real_evidence" if evidence_required else "stock_broll"


def build_remotion_stub(paragraph: str, rule: dict[str, object], visual_mode: str) -> dict[str, object]:
    words = re.findall(r"[\w\u4e00-\u9fff]{2,20}", paragraph)
    short_text = " ".join(words[:8]) if words else str(rule["label"])
    template = {
        "能力演示": "terminal_to_cards",
        "概念定义": "hero_title",
        "技能生态": "timeline_flow",
        "结尾引导": "hero_title",
    }.get(str(rule["label"]), "metric_cards")

    return {
        "style_direction": None,
        "template": template,
        "motion_goal": str(rule["communication_goal"]),
        "duration_sec": 4 if visual_mode == "hybrid" else 5,
        "on_screen_text": short_text,
        "props": {},
        "supporting_assets": [],
    }


def build_shot_brief(paragraph: str, rule: dict[str, object], visual_mode: str) -> dict[str, object]:
    lower = paragraph.lower()
    framing = "medium_wide"
    if "特写" in paragraph or "close-up" in lower:
        framing = "close_up"
    elif "远景" in paragraph or "wide" in lower:
        framing = "wide"

    camera_motion = "static"
    if "推进" in paragraph or "push" in lower:
        camera_motion = "slow_push_in"
    elif "拉远" in paragraph or "pull" in lower:
        camera_motion = "slow_pull_out"
    elif "tracking" in lower or "跟拍" in paragraph:
        camera_motion = "tracking"

    scene_mood = "clean, readable, editor-friendly"
    if "夜" in paragraph or "night" in lower:
        scene_mood = "night, focused, cinematic"
    elif "科技" in paragraph or "tech" in lower:
        scene_mood = "clean, futuristic, premium"

    search_status = "search_first"
    generation_fallback = "video_prompt" if visual_mode in {"shot_library", "video_prompt", "hybrid"} else None

    return {
        "shot_type": SHOT_TYPE_MAP.get(str(rule["label"]), "insert_shot"),
        "framing": framing,
        "camera_motion": camera_motion,
        "scene_subject": " ".join(re.findall(r"[\w\u4e00-\u9fff]{2,20}", paragraph)[:8]) or str(rule["label"]),
        "scene_mood": scene_mood,
        "must_show": list(rule["must_show"]),
        "disallowed_noise": list(DEFAULT_SPEC["disallowed_noise"]),
        "search_status": search_status,
        "generation_fallback": generation_fallback,
    }


def build_video_prompt_stub(paragraph: str, shot_brief: dict[str, object]) -> dict[str, object]:
    subject = shot_brief["scene_subject"]
    framing = str(shot_brief["framing"]).replace("_", " ")
    camera_motion = str(shot_brief["camera_motion"]).replace("_", " ")
    mood = shot_brief["scene_mood"]
    prompt = (
        f"{subject}, {framing} framing, {camera_motion} camera, "
        f"{mood}, clean premium visual style, suitable for short-form video editing"
    )
    return {
        "prompt_purpose": "真实镜头搜索较弱时的生成兜底",
        "prompt": prompt,
        "negative_keywords": ["watermark", "logo clutter", "blurry", "messy composition"],
        "duration_hint": "3-4 秒",
        "style_family": "科技电影感写实",
    }


def build_markdown(segments: list[dict[str, object]]) -> str:
    lines = ["# 素材简报", ""]
    for segment in segments:
        lines.extend(
            [
                f"## {segment['segment_id']}_{segment['segment_label']}",
                "",
                f"- 传播目标: {segment['communication_goal']}",
                f"- 情绪基调: {segment['emotional_tone']}",
                f"- 是否需要证据: {segment['evidence_required']}",
                f"- 候选视觉模式: {segment['visual_mode_candidate']}",
                f"- 所需素材类型: {', '.join(segment['material_types_needed'])}",
                f"- 目标平台: {', '.join(segment['search_brief']['target_platforms'])}",
                f"- 必须出现: {', '.join(segment['search_brief']['must_show'])}",
                f"- 禁止噪音: {', '.join(segment['search_brief']['disallowed_noise'])}",
                f"- 建议视觉风格: {segment['search_brief']['suggested_visual_style']}",
                f"- 候选关键词: {', '.join(segment['search_brief']['keywords'])}",
                "",
            ]
        )
        if segment.get("remotion_style_confirmation_required"):
            lines.extend(
                [
                    "### Remotion风格确认",
                    "",
                    "- 是否必需: 是",
                    f"- 风格选项: {', '.join(segment['remotion_style_options'])}",
                    f"- 建议模板: {segment['remotion_brief_stub']['template']}",
                    "",
                ]
            )
        if segment.get("shot_brief_stub"):
            lines.extend(
                [
                    "### 镜头需求",
                    "",
                    f"- 镜头类型: {segment['shot_brief_stub']['shot_type']}",
                    f"- 构图: {segment['shot_brief_stub']['framing']}",
                    f"- 运镜: {segment['shot_brief_stub']['camera_motion']}",
                    f"- 场景情绪: {segment['shot_brief_stub']['scene_mood']}",
                    f"- 生成兜底: {segment['shot_brief_stub']['generation_fallback']}",
                    "",
                ]
            )
        if segment.get("video_prompt_stub"):
            lines.extend(
                [
                    "### 视频提示词兜底",
                    "",
                    f"- 提示词: {segment['video_prompt_stub']['prompt']}",
                    f"- 负面关键词: {', '.join(segment['video_prompt_stub']['negative_keywords'])}",
                    "",
                ]
            )
        lines.extend(
            [
                "### 原始文案",
                "",
                segment["source_text"],
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a starter material brief from a script.")
    parser.add_argument("--script-file", required=True, help="Path to the input script text file.")
    parser.add_argument("--output-dir", required=True, help="Directory for the generated brief files.")
    args = parser.parse_args()

    script_path = Path(args.script_file).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    text = script_path.read_text(encoding="utf-8")
    paragraphs = split_paragraphs(text)
    segments = [build_segment(paragraph, index, len(paragraphs)) for index, paragraph in enumerate(paragraphs)]

    json_path = output_dir / "素材简报.json"
    md_path = output_dir / "素材简报.md"
    json_path.write_text(json.dumps({"segments": segments}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(build_markdown(segments) + "\n", encoding="utf-8")

    print(f"Wrote: {json_path}")
    print(f"Wrote: {md_path}")
    print(f"Segments: {len(segments)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
