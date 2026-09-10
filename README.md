# Humanizer for Codex

Humanizer edits stiff, formulaic prose while preserving the writer's meaning and
voice. Use it for documents, emails, blog posts, comments, and pull request
descriptions. It is a standalone skill with 25 editing patterns and no runtime
dependencies, API keys, or model setting to configure.

## Install

Clone this repository and run the installer from its root. The installer requires
Python 3.10 or newer and works on Windows, macOS, and Linux.

```sh
git clone https://github.com/CaiCheng-Li/humanizer-codex.git
cd humanizer-codex
python scripts/install.py
```

Use `python3` if that is your Python command. The installer copies `SKILL.md`,
`agents/openai.yaml`, and `LICENSE` into `~/.agents/skills/humanizer/`. It leaves the
checkout and other skills alone and refuses to overwrite an existing destination.
To replace an older installation, move its `humanizer` folder to a backup location
outside your skill directories, then run the installer again.

For an installation that uses a different skill directory, pass its path explicitly:

```powershell
python scripts/install.py --skills-dir "$env:USERPROFILE/.codex/skills"
```

```sh
python3 scripts/install.py --skills-dir "${CODEX_HOME:-$HOME/.codex}/skills"
```

For a manual install, create a `humanizer` folder in your skill directory and copy
the same three files, keeping the `agents` subdirectory. Keep only one installation
named `humanizer` in the locations your client scans.

Codex documents `~/.agents/skills` as a user skill location. In the CLI or IDE
extension, use `/skills` or type `$` to select a skill. If Humanizer does not appear
after installation, restart Codex. See the [official skill documentation](https://learn.chatgpt.com/docs/build-skills)
for discovery locations and client details.

## Use

Paste text with an explicit invocation:

```text
$humanizer Rewrite this paragraph to sound natural:

At its core, this groundbreaking update empowers users to export CSV files.
```

Expected rewrite:

> This update lets users export CSV files.

To edit a local file:

```text
$humanizer Edit the prose in docs/launch.md. Keep the technical details and links.
```

To request suggestions without changing a file:

```text
$humanizer Review README.md for stiff or repetitive prose. Suggest edits only.
```

To match your voice:

```text
$humanizer Rewrite the draft below using my sample's voice.

Writing sample:
[A few paragraphs of your writing]

Draft:
[The text to edit]
```

To prepare prose within a coding task:

```text
$humanizer Polish this pull request description. Keep the before-and-after
behavior and test results exactly as stated. Return only the revised description.
```

Humanizer also supports automatic selection when a request matches its description,
such as "Humanize this text" or "Remove the AI tells from this draft." Routine
implementation work and authorship detection are outside its scope.

## Editing behavior

Humanizer reads the passage, rewrites it, and checks the result against the source.
It returns one finished rewrite by default. Ask for a comparison or explanation
when you want one. For file edits, it writes the final prose and gives a short summary.
Review requests produce suggestions without changing files.

Facts, uncertainty, attribution, and the writer's position must survive the edit.
Personal writing keeps its humor and opinions without adding invented experiences.
Technical writing keeps exact identifiers, commands, code, frontmatter, links, and
requirements. A prose edit does not verify the source's facts or authorize publishing.

The patterns are editorial prompts, not an authorship test. An ordinary word, dash,
passive sentence, or list of three items is not enough reason to rewrite it. User
instructions and writing samples take precedence over general style preferences.

## The 25 patterns

Start with staging, then review rhythm, claims, formatting, and drafting leftovers.
Each pattern in [SKILL.md](SKILL.md) includes an example and guidance on when to keep
the original construction.

### A. Staging instead of stating

| # | Pattern | Editing approach |
|---|---------|------------------|
| 1 | Not X but Y | State the point directly; keep real distinctions. |
| 2 | One-line closers and dramatic fragments | Cut repeated conclusions; keep new information. |
| 3 | Sayings that sound deep | Replace grand framing with the actual claim. |
| 4 | Staged run-up before the point | Remove announcements before routine statements. |
| 5 | Arguing with no one | Cut invented objections; keep real tradeoffs. |

### B. Rhythm by rule

| # | Pattern | Editing approach |
|---|---------|------------------|
| 6 | Forced triads | Cut overlapping ideas; keep all distinct items. |
| 7 | Repeated sentence openings | Combine related actions when repetition gets in the way. |
| 8 | Dashes as the universal connector | Clarify clause relationships; keep useful punctuation. |
| 9 | Stacked qualifiers | Remove redundant hedges without changing certainty. |
| 10 | Hyphenated pairs everywhere | Prefer direct descriptions; preserve standard terms. |
| 11 | Passive voice and missing subjects | Name known actors when useful. |

### C. Inflation and borrowed authority

| # | Pattern | Editing approach |
|---|---------|------------------|
| 12 | Overused AI words | Replace vague stock language with precise words. |
| 13 | Inflated significance | Keep events and plans; remove empty grandeur. |
| 14 | Vague connection or association | Use only relationships established by the source. |
| 15 | Shallow -ing riders | Cut empty commentary; preserve consequences. |
| 16 | Sales language | Describe supported features and benefits. |
| 17 | Borrowed authority | Preserve attribution; flag claims that need support. |
| 18 | Avoiding is, are, and has | Use direct verbs without changing quantities or meaning. |

### D. Formatting by rule

| # | Pattern | Editing approach |
|---|---------|------------------|
| 19 | Bold as decoration | Keep formatting that helps readers scan. |
| 20 | Decorative headings | Follow document conventions and preserve link anchors. |
| 21 | Curly quotation marks | Match the target format; preserve literal text. |

### E. Leftovers from the chat and the draft

| # | Pattern | Editing approach |
|---|---------|------------------|
| 22 | Chatbot residue | Remove chat wrappers from standalone prose. |
| 23 | Knowledge-limit disclaimers and guesses | Keep meaningful limits; never turn guesses into facts. |
| 24 | A heading repeated in the first sentence | Cut redundant introductions. |
| 25 | Writing about the previous version | Describe current behavior unless the document concerns change. |

## Example: technical prose

Before:

> Here's what you need to know: this isn't just an export feature, it's a seamless
> way to save your results. The CSV export includes names, dates, and totals,
> showcasing our commitment to a robust workflow. Files expire after 24 hours.
> The export may take up to 30 seconds for large reports. That's the real win.

After:

> The CSV export lets you save your results with names, dates, and totals. Files
> expire after 24 hours. Exporting large reports may take up to 30 seconds.

The rewrite keeps all three exported fields, the expiry, the time limit, and the
qualification about large reports. It removes framing and praise without inventing
a benchmark or changing what the feature does.

## Maintain the package

`SKILL.md` is the only skill entrypoint. `agents/openai.yaml` supplies its display
name, description, and default prompt. The installer copies only the runtime files
and license. The repository itself has no build step.

Run these commands from the `humanizer-codex` repository root:

```sh
python -m pip install -r requirements-dev.txt
python scripts/validate-package.py
python -B -m unittest discover -s tests -v
npx --yes skills@1.5.20 add . --list
```

Python and PyYAML are needed for the package checks. Node.js and npm are needed only
for the discovery check. CI runs the Python checks on Windows and Linux and checks
skill discovery on Linux.

Keep `metadata.version` in `SKILL.md` equal to the first version entry below. Keep
pattern numbers, names, README tables, and section references in sync. Add a short
version note for behavior changes. The package validator checks these shared values
and parses both YAML files. Script tests cover installation and invalid packages.
They do not measure writing quality; try real editing requests when changing the prompt.

The inherited, tracked `AGENTS.md` still describes the upstream package. It is
preserved under the workspace rule against relocating tracked assistant
configuration. This README describes the current package and checks.

## Version history

- **4.0.0** - Rewrote the skill for Codex prose workflows and local file editing.
  Replaced the plugin and marketplace package with a standalone installation.
  Rewrote all 25 patterns and examples, made final-only output the default, added
  review-only behavior, and tightened preservation of facts and technical content.
  Removed blanket punctuation rules and permission to invent personal reactions.
  Added YAML validation, installer tests, and checks on Windows and Linux.
- **3.0.0** - Upstream baseline with 25 patterns grouped into five sections.
  Earlier releases remain in the [upstream history](https://github.com/blader/humanizer).

## Sources and license

Adapted from [Humanizer](https://github.com/blader/humanizer). The pattern catalog
draws on [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing).

[MIT license](LICENSE). The original copyright notice is preserved.
