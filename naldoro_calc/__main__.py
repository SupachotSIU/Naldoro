"""CLI: python -m naldoro_calc <command> [input.json | -]

อ่านพารามิเตอร์เป็น JSON object จากไฟล์ (หรือ stdin ถ้าไม่ระบุ/ใส่ '-')
แล้วพิมพ์ผลลัพธ์เป็น JSON.
"""

from __future__ import annotations

import json
import sys

from . import (
    analyze_policy,
    compare_plans,
    human_life_value,
    needs_analysis,
    retirement_plan,
    tax_with_insurance,
)

COMMANDS = {
    "needs": needs_analysis,
    "hlv": human_life_value,
    "tax": tax_with_insurance,
    "retirement": retirement_plan,
    "policy": analyze_policy,
    "compare": compare_plans,
}


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] not in COMMANDS:
        print(__doc__, file=sys.stderr)
        print("commands: " + ", ".join(COMMANDS), file=sys.stderr)
        return 2
    command, source = argv[0], (argv[1] if len(argv) > 1 else "-")
    try:
        if source == "-":
            params = json.load(sys.stdin)
        else:
            with open(source, encoding="utf-8") as fh:
                params = json.load(fh)
        params.pop("_comment", None)
        result = COMMANDS[command](**params)
    except (TypeError, ValueError, KeyError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
