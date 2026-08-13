from __future__ import annotations

import json

from app.prompts import prompt_registry


if __name__ == "__main__":
    print(json.dumps(prompt_registry.metadata(), ensure_ascii=False, indent=2))
