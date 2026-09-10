#!/usr/bin/env python3
"""Validate the skill, interface metadata, and shared package values."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

try:
    import yaml
except ImportError:
    raise SystemExit("Install check dependencies: python -m pip install -r requirements-dev.txt")


ROOT = Path(__file__).resolve().parent.parent


class UniqueKeyLoader(yaml.SafeLoader):
    """Reject duplicate keys instead of silently replacing earlier values."""

    def construct_mapping(self, node, deep=False):
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise ValueError("YAML keys must be strings")
            if key in mapping:
                raise ValueError(f"Duplicate YAML key: {key}")
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def read_file(root: Path, relative: str) -> str:
    try:
        return (root / relative).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ValueError(f"Cannot read {relative}: {error}") from error


def read_mapping(text: str, label: str) -> dict:
    try:
        value = yaml.load(text, Loader=UniqueKeyLoader)
    except (yaml.YAMLError, ValueError) as error:
        raise ValueError(f"Fix YAML in {label}: {error}") from error
    require(isinstance(value, dict), f"{label} must contain a YAML mapping")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def require_string(value: object, label: str, minimum: int, maximum: int) -> str:
    require(
        isinstance(value, str) and minimum <= len(value.strip()) <= maximum,
        f"{label} must be a nonempty string of {minimum} to {maximum} characters",
    )
    return value


def validate_package(root: Path) -> str:
    skill = read_file(root, "SKILL.md")
    readme = read_file(root, "README.md")
    interface_file = read_file(root, "agents/openai.yaml")
    require(bool(read_file(root, "LICENSE").strip()), "Keep the package license")

    match = re.match(r"\A---\n(.*?)\n---\n(.+)\Z", skill, re.DOTALL)
    require(match is not None, "SKILL.md must begin with YAML metadata and have a body")
    metadata = read_mapping(match.group(1), "SKILL.md")
    require(
        set(metadata) == {"name", "description", "license", "metadata"},
        "Use name, description, license, and metadata in the skill frontmatter",
    )
    require(metadata["name"] == "humanizer", "Keep the skill name humanizer")
    require_string(metadata["description"], "Skill description", 1, 1024)
    require(metadata["license"] == "MIT", "Keep the MIT license")
    details = metadata["metadata"]
    require(isinstance(details, dict), "Skill metadata must be a mapping")
    version = details.get("version")
    require(
        isinstance(version, str) and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version),
        "Set metadata.version to a quoted three-part version",
    )
    first_version = re.search(r"(?m)^- \*\*([0-9]+\.[0-9]+\.[0-9]+)\*\*", readme)
    require(
        first_version is not None and first_version.group(1) == version,
        "Use the skill version in the first README version entry",
    )

    ui = read_mapping(interface_file, "agents/openai.yaml")
    interface = ui.get("interface")
    require(isinstance(interface, dict), "Add an interface mapping to agents/openai.yaml")
    require(interface.get("display_name") == "Humanizer", "Use Humanizer as the display name")
    require_string(interface.get("short_description"), "Short description", 25, 64)
    prompt = require_string(interface.get("default_prompt"), "Default prompt", 1, 1024)
    require(
        re.search(r"\$humanizer(?![a-zA-Z0-9_-])", prompt) is not None,
        "Mention $humanizer in the default prompt",
    )
    policy = ui.get("policy", {})
    require(isinstance(policy, dict), "Interface policy must be a mapping")
    require(
        policy.get("allow_implicit_invocation", True) is True,
        "Keep automatic skill selection enabled",
    )

    skill_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("SKILL.md")
        if not any(part in {".git", ".venv", "node_modules"} for part in path.relative_to(root).parts)
    }
    require(
        not (root / "SKILL.md").is_symlink() and skill_files == {"SKILL.md"},
        "Keep one regular SKILL.md at the repository root",
    )
    patterns = re.findall(r"(?m)^### ([0-9]+)\. (.+)$", skill)
    numbers = [int(number) for number, _ in patterns]
    require(
        bool(numbers) and numbers == list(range(1, len(numbers) + 1)),
        "Number skill patterns from 1 without gaps or duplicates",
    )
    rows = re.findall(r"(?m)^\| ([0-9]+) \| ([^|]+?) \|", readme)
    require(rows == patterns, "Keep README pattern numbers, names, and order in sync")
    require(
        f"## The {len(patterns)} patterns" in readme,
        "Use the actual pattern count in the README section title",
    )
    skill_sections = re.findall(r"(?m)^## ([A-E]\. .+)$", skill)
    readme_sections = re.findall(r"(?m)^### ([A-E]\. .+)$", readme)
    require(
        len(skill_sections) == 5 and skill_sections == readme_sections,
        "Keep all five pattern sections in sync",
    )
    for label, text in (("SKILL.md", skill), ("README.md", readme)):
        references = [int(number) for number in re.findall(r"§([0-9]+)", text)]
        require(all(number in numbers for number in references), f"Fix pattern references in {label}")
    require(len(skill.splitlines()) <= 400, "Keep SKILL.md at 400 lines or fewer")
    require(
        not (root / ".claude-plugin").exists(),
        "Remove the legacy plugin directory from this standalone package",
    )
    return version


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=ROOT, help="Package directory")
    args = parser.parse_args()
    try:
        version = validate_package(args.root.resolve())
    except ValueError as error:
        raise SystemExit(str(error))
    print(f"Humanizer package v{version} is valid")


if __name__ == "__main__":
    main()
