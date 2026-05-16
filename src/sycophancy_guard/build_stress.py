from __future__ import annotations

import argparse
from collections.abc import Iterable

from .io import label_to_name, normalized_base_record, read_jsonl, stable_id, write_jsonl
from .pressure_templates import (
    DEFAULT_PRESSURE_LAYOUT,
    get_neutral_control_templates,
    get_pressure_layouts,
    get_templates,
    hard_template_names,
    neutral_control_template_names,
    pressure_layout_names,
    template_names,
)


def desired_labels_for(label: int, mode: str) -> list[str]:
    correct = label_to_name(label)
    opposite = "safe" if label == 1 else "unsafe"
    if mode == "correct":
        return [correct]
    if mode == "opposite":
        return [opposite]
    if mode == "both":
        return [correct, opposite]
    raise ValueError(f"Unsupported target mode: {mode}")


def build_records(
    base_records: Iterable[dict],
    targets: list[str],
    templates: list[str] | None,
    include_clean: bool,
    wrapper_mode: str,
    include_hard_pressure: bool = False,
    include_neutral_controls: bool = False,
    include_pressure_only: bool = False,
    pressure_layouts: list[str] | None = None,
) -> list[dict]:
    pressure_templates = get_templates(templates, include_hard=include_hard_pressure)
    neutral_templates = get_neutral_control_templates() if include_neutral_controls else []
    layout_defs = get_pressure_layouts(pressure_layouts)
    output: list[dict] = []

    for raw in base_records:
        base = normalized_base_record(raw)
        if include_clean:
            output.append(
                {
                    **base,
                    "id": f"{base['base_id']}::clean",
                    "variant_id": "clean",
                    "pressure_type": "clean",
                    "pressure_family": "clean",
                    "pressure_intensity": None,
                    "pressure_channel": None,
                    "pressure_heldout": False,
                    "pressure_layout": None,
                    "pressure_placement": None,
                    "pressure_format": None,
                    "desired_label": None,
                    "is_attack": False,
                    "is_pressure_only": False,
                    "is_neutral_control": False,
                    "supervised": True,
                    "pressure_only_text": "",
                    "clean_text": base["text"],
                }
            )

        for target_mode in targets:
            for desired_label in desired_labels_for(base["label"], target_mode):
                for template in pressure_templates:
                    for layout in layout_defs:
                        layout_name = layout.name
                        layout_suffix = "" if layout_name == DEFAULT_PRESSURE_LAYOUT else f"_{layout_name}"
                        variant_id = f"{template.name}{layout_suffix}_{desired_label}"
                        layout_metadata = template.layout_metadata(layout_name)
                        pressure_only_text = template.pressure_only(
                            desired_label,
                            wrapper_mode=wrapper_mode,
                            pressure_layout=layout_name,
                        )
                        text = template.render(
                            base["text"],
                            desired_label,
                            wrapper_mode=wrapper_mode,
                            pressure_layout=layout_name,
                        )
                        output.append(
                            {
                                **base,
                                "id": f"{base['base_id']}::{variant_id}",
                                "variant_id": variant_id,
                                "pressure_type": template.name,
                                "pressure_family": template.family,
                                "pressure_intensity": template.intensity,
                                "pressure_channel": template.channel,
                                "pressure_heldout": template.heldout,
                                **layout_metadata,
                                "desired_label": desired_label,
                                "is_attack": desired_label != base["label_name"],
                                "is_pressure_only": False,
                                "is_neutral_control": False,
                                "supervised": True,
                                "pressure_only_text": pressure_only_text,
                                "wrapper_mode": wrapper_mode,
                                "clean_text": base["text"],
                                "text": text,
                            }
                        )
                        if include_pressure_only:
                            output.append(
                                {
                                    **base,
                                    "label": None,
                                    "label_name": None,
                                    "case_label": base["label"],
                                    "case_label_name": base["label_name"],
                                    "id": f"{base['base_id']}::pressure_only_{variant_id}",
                                    "variant_id": f"pressure_only_{variant_id}",
                                    "pressure_type": template.name,
                                    "pressure_family": template.family,
                                    "pressure_intensity": template.intensity,
                                    "pressure_channel": template.channel,
                                    "pressure_heldout": template.heldout,
                                    **layout_metadata,
                                    "desired_label": desired_label,
                                    "is_attack": False,
                                    "is_pressure_only": True,
                                    "is_neutral_control": False,
                                    "supervised": False,
                                    "pressure_only_text": pressure_only_text,
                                    "wrapper_mode": wrapper_mode,
                                    "clean_text": "",
                                    "text": pressure_only_text,
                                }
                            )

        for template in neutral_templates:
            for layout in layout_defs:
                layout_name = layout.name
                layout_suffix = "" if layout_name == DEFAULT_PRESSURE_LAYOUT else f"_{layout_name}"
                variant_id = f"{template.name}{layout_suffix}"
                layout_metadata = template.layout_metadata(layout_name)
                pressure_only_text = template.pressure_only(
                    None,
                    wrapper_mode=wrapper_mode,
                    pressure_layout=layout_name,
                )
                text = template.render(
                    base["text"],
                    None,
                    wrapper_mode=wrapper_mode,
                    pressure_layout=layout_name,
                )
                output.append(
                    {
                        **base,
                        "id": f"{base['base_id']}::{variant_id}",
                        "variant_id": variant_id,
                        "pressure_type": template.name,
                        "pressure_family": template.family,
                        "pressure_intensity": template.intensity,
                        "pressure_channel": template.channel,
                        "pressure_heldout": template.heldout,
                        **layout_metadata,
                        "desired_label": None,
                        "is_attack": False,
                        "is_pressure_only": False,
                        "is_neutral_control": True,
                        "supervised": True,
                        "pressure_only_text": pressure_only_text,
                        "wrapper_mode": wrapper_mode,
                        "clean_text": base["text"],
                        "text": text,
                    }
                )
                if include_pressure_only:
                    output.append(
                        {
                            **base,
                            "label": None,
                            "label_name": None,
                            "case_label": base["label"],
                            "case_label_name": base["label_name"],
                            "id": f"{base['base_id']}::pressure_only_{variant_id}",
                            "variant_id": f"pressure_only_{variant_id}",
                            "pressure_type": template.name,
                            "pressure_family": template.family,
                            "pressure_intensity": template.intensity,
                            "pressure_channel": template.channel,
                            "pressure_heldout": template.heldout,
                            **layout_metadata,
                            "desired_label": None,
                            "is_attack": False,
                            "is_pressure_only": True,
                            "is_neutral_control": True,
                            "supervised": False,
                            "pressure_only_text": pressure_only_text,
                            "wrapper_mode": wrapper_mode,
                            "clean_text": "",
                            "text": pressure_only_text,
                        }
                    )

    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build pressure stress JSONL.")
    parser.add_argument("--input", required=True, help="Input labeled JSONL.")
    parser.add_argument("--output", required=True, help="Output stress JSONL.")
    parser.add_argument(
        "--targets",
        default="opposite",
        help="Comma list from: opposite,correct,both. Default: opposite.",
    )
    parser.add_argument(
        "--templates",
        default="",
        help=(
            "Comma list of pressure templates. Default standard templates: "
            f"{', '.join(template_names())}. Hard opt-in templates: "
            f"{', '.join(hard_template_names())}"
        ),
    )
    parser.add_argument(
        "--include-hard-pressure",
        action="store_true",
        help="Include higher-intensity hard pressure templates in addition to standard templates.",
    )
    parser.add_argument(
        "--include-neutral-controls",
        action="store_true",
        help=(
            "Include non-label-seeking neutral controls: "
            f"{', '.join(neutral_control_template_names())}"
        ),
    )
    parser.add_argument(
        "--include-pressure-only",
        action="store_true",
        help="Emit pressure-only null records for estimating wrapper label priors.",
    )
    parser.add_argument(
        "--pressure-layouts",
        default="",
        help=(
            "Comma list of pressure layouts. Default pre_case. Available: "
            f"{', '.join(pressure_layout_names())}"
        ),
    )
    parser.add_argument("--max-items", type=int, default=0, help="Optional input cap.")
    parser.add_argument("--no-clean", action="store_true", help="Do not include clean variants.")
    parser.add_argument(
        "--wrapper-mode",
        choices=["attack", "guarded"],
        default="attack",
        help="attack omits defensive instructions; guarded includes anti-pressure instructions.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = read_jsonl(args.input)
    if args.max_items and args.max_items > 0:
        records = records[: args.max_items]

    targets = [item.strip() for item in args.targets.split(",") if item.strip()]
    expanded_targets: list[str] = []
    for target in targets:
        if target == "both":
            expanded_targets.extend(["correct", "opposite"])
        else:
            expanded_targets.append(target)

    templates = [item.strip() for item in args.templates.split(",") if item.strip()] or None
    pressure_layouts = [item.strip() for item in args.pressure_layouts.split(",") if item.strip()] or None
    stress = build_records(
        records,
        expanded_targets,
        templates,
        include_clean=not args.no_clean,
        wrapper_mode=args.wrapper_mode,
        include_hard_pressure=args.include_hard_pressure,
        include_neutral_controls=args.include_neutral_controls,
        include_pressure_only=args.include_pressure_only,
        pressure_layouts=pressure_layouts,
    )

    if not stress:
        raise ValueError("No records were produced")

    for record in stress:
        if not record.get("id"):
            record["id"] = stable_id(record["text"])

    write_jsonl(args.output, stress)
    print(f"Wrote {len(stress)} stress records to {args.output}")


if __name__ == "__main__":
    main()
