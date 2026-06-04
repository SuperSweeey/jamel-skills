#!/usr/bin/env python3
"""Generate infographic prompts for Gemini/Nanobanana from a material brief."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


STYLE_BLOCK = (
    "Style: modern minimalist vector illustration, clean smooth vector lines, "
    "flat shapes, simplified details, cute chibi characters, rounded forms, "
    "friendly robot and human figures, clean composition, high readability, "
    "bright but controlled palette, minimal background, no photorealism, no 3D render, "
    "no clutter, no gritty texture, no busy UI, suitable for a short-form video infographic."
)


LABEL_SCENE_MAP = {
    "concept_definition": (
        "concept card",
        "Use one central cute robot or agent character with 2 to 4 supporting labels or visual bubbles.",
    ),
    "capability_demo": (
        "workflow card",
        "Use a step-based flow with arrows showing the agent operating tools, browser, or files.",
    ),
    "skill_ecosystem": (
        "workflow card",
        "Show one workflow being packaged into a reusable skill and shared outward to other cute agent helpers.",
    ),
    "risk_warning": (
        "tradeoff card",
        "Show a clean visual contrast between capability and risk using a balanced layout.",
    ),
    "real_experience": (
        "comparison card",
        "Compare expectation vs reality or automation vs human supervision in a simple split layout.",
    ),
    "opening_heat_proof": (
        "supporting card",
        "Use this only as a support visual, not as a replacement for real evidence.",
    ),
    "closing_cta": (
        "outro card",
        "Use a simple inviting scene with one cute mascot and a clean call-to-action composition.",
    ),
}


def should_generate(segment: dict[str, object]) -> tuple[bool, str]:
    label = str(segment.get("segment_label", ""))
    evidence_required = str(segment.get("evidence_required", "no")).lower()
    communication_goal = str(segment.get("communication_goal", "")).lower()

    if label in {"concept_definition", "skill_ecosystem"}:
        return True, "abstract explanation"
    if label == "capability_demo" and "show what it can do" in communication_goal:
        return True, "workflow explanation"
    if label == "risk_warning":
        return True, "tradeoff summary"
    if label == "real_experience":
        return True, "comparison support"
    if evidence_required == "yes" and label == "opening_heat_proof":
        return False, "needs real evidence first"
    if label == "closing_cta":
        return True, "supporting outro visual"
    return False, "better served by sourced material"


def build_prompt(segment: dict[str, object]) -> dict[str, object]:
    label = str(segment["segment_label"])
    scene_type, composition_hint = LABEL_SCENE_MAP.get(
        label,
        ("infographic card", "Use one focal point and a clean editorial composition."),
    )

    text = str(segment.get("source_text", "")).strip()
    goal = str(segment.get("communication_goal", "")).strip()
    tone = str(segment.get("emotional_tone", "")).strip()
    must_show = ", ".join(segment.get("search_brief", {}).get("must_show", []))
    keywords = ", ".join(segment.get("search_brief", {}).get("keywords", [])[:8])

    prompt = (
        f"Create a {scene_type} infographic about: {goal}. "
        f"Core script idea: {text} "
        f"Composition: {composition_hint} "
        f"Must communicate: {must_show}. "
        f"Tone: {tone}. "
        f"Helpful visual cues: {keywords}. "
        f"{STYLE_BLOCK}"
    )

    negative_prompt = (
        "Avoid photorealism, avoid dark cyberpunk aesthetics, avoid complex background, "
        "avoid tiny unreadable text, avoid generic futuristic HUD clutter, avoid realistic human anatomy, "
        "avoid brand logos, avoid ad-like composition."
    )

    return {
        "segment_id": segment["segment_id"],
        "segment_label": label,
        "scene_type": scene_type,
        "why_infographic": should_generate(segment)[1],
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "suggested_filename": f"{segment['segment_id']}_{label}_infographic_prompt.txt",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate infographic prompts from a material brief JSON.")
    parser.add_argument("--brief-json", required=True, help="Path to material-brief.json.")
    parser.add_argument("--output-dir", required=True, help="Directory for generated prompt files.")
    args = parser.parse_args()

    brief_path = Path(args.brief_json).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    data = json.loads(brief_path.read_text(encoding="utf-8"))
    segments = data.get("segments", [])

    prompts = []
    for segment in segments:
        use_it, reason = should_generate(segment)
        if not use_it:
            continue
        item = build_prompt(segment)
        item["why_infographic"] = reason
        prompts.append(item)
        prompt_path = output_dir / item["suggested_filename"]
        prompt_path.write_text(
            item["prompt"] + "\n\nNegative prompt:\n" + item["negative_prompt"] + "\n",
            encoding="utf-8",
        )

    summary = {"style": STYLE_BLOCK, "prompts": prompts}
    (output_dir / "infographic-prompts.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Generated prompts: {len(prompts)}")
    print(f"Output dir: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
