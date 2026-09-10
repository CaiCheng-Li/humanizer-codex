#!/usr/bin/env python3
"""Install the standalone Humanizer skill without replacing existing files."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SKILL_NAME = "humanizer"
PACKAGE_FILES = ("SKILL.md", "agents/openai.yaml", "LICENSE")


def install(source: Path, skills_dir: Path) -> Path:
    """Copy the runtime files and license into a new skill directory."""
    # Read every source before creating the destination so missing files leave no install.
    payload = {relative: (source / relative).read_bytes() for relative in PACKAGE_FILES}
    destination = skills_dir.expanduser().resolve() / SKILL_NAME
    try:
        destination.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        raise FileExistsError(
            f"Destination already exists: {destination}. "
            "Move it to a backup location before installing again."
        ) from None
    for relative, content in payload.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skills-dir",
        type=Path,
        default=Path.home() / ".agents" / "skills",
        help="Parent skill directory (default: ~/.agents/skills)",
    )
    args = parser.parse_args()
    try:
        destination = install(ROOT, args.skills_dir)
    except OSError as error:
        raise SystemExit(f"Installation failed: {error}")
    print(f"Installed Humanizer at {destination}")
    print("Invoke it with $humanizer. Restart your client if the skill does not appear.")


if __name__ == "__main__":
    main()
