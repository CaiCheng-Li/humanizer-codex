"""Exercise package failures and installation without touching user skill folders."""

from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_script("validator", "validate-package.py")
installer = load_script("installer", "install.py")


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="humanizer-tests-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.package = self.directory / "source"
        for relative in (*installer.PACKAGE_FILES, "README.md"):
            target = self.package / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)

    def replace(self, relative: str, before: str, after: str):
        path = self.package / relative
        original = path.read_text(encoding="utf-8")
        self.assertIn(before, original)
        path.write_text(original.replace(before, after, 1), encoding="utf-8")

    def test_current_package(self):
        self.assertEqual(validator.validate_package(self.package), "4.0.0")

    def test_invalid_packages(self):
        cases = [
            ("SKILL.md", "name: humanizer", "name: [humanizer", "Fix YAML"),
            ("SKILL.md", "name: humanizer", "name: humanizer\nname: duplicate", "Duplicate YAML key"),
            ("SKILL.md", "  version: \"4.0.0\"", "version: \"4.0.0\"", "frontmatter"),
            ("README.md", "**4.0.0**", "**4.0.1**", "first README version"),
            ("SKILL.md", "### 2. ", "### 3. ", "without gaps"),
            ("README.md", "| 1 | Not X but Y |", "| 1 | Different name |", "pattern numbers, names"),
            ("README.md", "## The 25 patterns", "## The 24 patterns", "actual pattern count"),
            ("README.md", "## Editing behavior", "## Editing behavior\n\nSee §26.", "pattern references"),
            ("agents/openai.yaml", "$humanizer", "$another-skill", "Mention $humanizer"),
            ("agents/openai.yaml", "$humanizer", "$humanizer-other", "Mention $humanizer"),
            ("agents/openai.yaml", 'display_name: "Humanizer"', "display_name: []", "display name"),
        ]
        for relative, before, after, message in cases:
            with self.subTest(relative=relative, change=after):
                path = self.package / relative
                original = path.read_bytes()
                try:
                    self.replace(relative, before, after)
                    with self.assertRaisesRegex(ValueError, re.escape(message)):
                        validator.validate_package(self.package)
                finally:
                    path.write_bytes(original)

    def test_plain_multiline_yaml_description(self):
        self.replace("SKILL.md", "description: >-", "description:")
        self.assertEqual(validator.validate_package(self.package), "4.0.0")

    def test_false_invocation_policy(self):
        path = self.package / "agents/openai.yaml"
        with path.open("a", encoding="utf-8") as stream:
            stream.write("\npolicy:\n  allow_implicit_invocation: false\n")
        with self.assertRaisesRegex(ValueError, "automatic skill selection"):
            validator.validate_package(self.package)

    def test_missing_interface(self):
        (self.package / "agents/openai.yaml").unlink()
        with self.assertRaisesRegex(ValueError, "Cannot read agents/openai.yaml"):
            validator.validate_package(self.package)

    def test_duplicate_skill(self):
        extra = self.package / "nested/SKILL.md"
        extra.parent.mkdir()
        extra.write_text("---\nname: duplicate\n---\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "one regular SKILL.md"):
            validator.validate_package(self.package)

    def test_installed_bytes_and_file_selection(self):
        (self.package / "AGENTS.md").write_text("Local instructions", encoding="utf-8")
        destination = installer.install(self.package, self.directory / "skills with spaces")
        self.assertEqual(destination.name, "humanizer")
        actual = {p.relative_to(destination).as_posix() for p in destination.rglob("*") if p.is_file()}
        self.assertEqual(actual, set(installer.PACKAGE_FILES))
        for relative in installer.PACKAGE_FILES:
            self.assertEqual((destination / relative).read_bytes(), (self.package / relative).read_bytes())

    def test_existing_install_is_preserved(self):
        parent = self.directory / "skills"
        destination = installer.install(self.package, parent)
        marker = destination / "SKILL.md"
        marker.write_bytes(b"User changes\r\n")
        with self.assertRaisesRegex(FileExistsError, "already exists"):
            installer.install(self.package, parent)
        self.assertEqual(marker.read_bytes(), b"User changes\r\n")

    def test_existing_file_is_preserved(self):
        parent = self.directory / "skills"
        parent.mkdir()
        destination = parent / "humanizer"
        destination.write_bytes(b"Keep this file")
        with self.assertRaises(FileExistsError):
            installer.install(self.package, parent)
        self.assertEqual(destination.read_bytes(), b"Keep this file")

    def test_missing_source_does_not_create_install(self):
        (self.package / "LICENSE").unlink()
        parent = self.directory / "skills"
        with self.assertRaises(FileNotFoundError):
            installer.install(self.package, parent)
        self.assertFalse(parent.exists())

    def test_installer_cli_without_site_packages(self):
        command = [
            sys.executable, "-S", str(ROOT / "scripts/install.py"),
            "--skills-dir", str(self.directory / "cli skills"),
        ]
        result = subprocess.run(command, cwd=self.directory, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("$humanizer", result.stdout)
        result = subprocess.run(command, cwd=self.directory, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already exists", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
