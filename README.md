# OpenCourse

OpenCourse is an OpenClaw-inspired, terminal-first learning platform for university teaching.

It ships as a polished CLI where students run weekly activities from modular skills (quiz, qna, guided-lab, python-test, dataset-explorer, hint, review), with local progress tracking and deterministic assessment checks.

The starter bundled module is **Big Data Processing**.

## Why OpenCourse

- OpenClaw-style skill folders with `SKILL.md` + YAML frontmatter
- Branded, modern CLI UX built with Typer + Rich
- Weekly coursepack model for lecturer publishing
- Local-first progress and deterministic checks
- Optional AI assistance via pluggable adapters (works fully without AI)
- Skill source precedence that favors local course content over bundled content

## Installation

```bash
python3 -m pip install opencourse
```

## Update

```bash
python3 -m pip install --upgrade opencourse
```

You can also run:

```bash
opencourse update
```

For development from this repo:

```bash
git clone <your-repo-url>
cd opencourse
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

## Quick Start

```bash
opencourse
opencourse module list
opencourse set module big-data-processing
opencourse learn
opencourse skills list
opencourse week 1
opencourse week open 1
opencourse lab lab-csv-basics
opencourse quiz quiz-intro-data
opencourse test test-task1
opencourse progress
opencourse update
```

## External Modules (GitHub)

OpenCourse can load teaching modules from external Git repositories.

```bash
opencourse module add https://github.com/warestack/bda
opencourse module list
opencourse set module big-data-processing
opencourse set week 1
opencourse set session 1
opencourse learn
```

Module lifecycle commands:

- `opencourse module add <git-url> [--ref main|tag|sha]`
- `opencourse module update <module-id>`
- `opencourse module update --all`
- `opencourse module remove <module-id>`
- `opencourse module sync`
- `opencourse module doctor <module-id>`
- `opencourse module validate <path>`
- `opencourse module create-template [path]`

## Command Surface

- `opencourse`
- `opencourse learn`
- `opencourse module list`
- `opencourse module current`
- `opencourse module set <id>`
- `opencourse set module <id>`
- `opencourse practice`
- `opencourse validate`
- `opencourse skills list`
- `opencourse skills show <name>`
- `opencourse skills enable <name>`
- `opencourse skills disable <name>`
- `opencourse skills validate <path>`
- `opencourse week list`
- `opencourse week open <n>`
- `opencourse week start <n>`
- `opencourse week <n>`
- `opencourse continue`
- `opencourse lab <name>`
- `opencourse quiz <name>`
- `opencourse test <name>`
- `opencourse ask [question]`
- `opencourse progress`
- `opencourse update`
- `opencourse init-skill`
- `opencourse init-week`
- `opencourse init-coursepack`
- `opencourse validate-coursepack <path>`

## Skills Structure (OpenClaw-Compatible)

Each skill is a folder:

```text
skill-name/
  SKILL.md
  skill.yaml (optional)
  config.json (optional)
  prompts/ (optional)
  tests/ (optional)
  datasets/ (optional)
  templates/ (optional)
  checker.py (optional)
```

`SKILL.md` uses YAML frontmatter:

```markdown
---
name: lab-csv-basics
description: Lab 1 Python and CSV basics
version: 0.1.0
tags: [lab,csv]
module: big-data-processing
week: 1
skill_type: guided-lab
runtime: {}
---
# Skill body
```

## Skill Loading Precedence

OpenCourse discovers skills in this order (first wins):

1. `./skills`
2. `./.agents/skills`
3. User-level skills directory (`$OPENCOURSE_HOME/skills` or `~/.opencourse/skills`)
4. Bundled built-in skills

This makes local lecturer/student overrides take precedence over defaults.

## Weekly Coursepacks

Coursepacks follow this structure:

```text
coursepacks/
  big-data-processing/
    course.yaml
    weeks/
      week-01/week.yaml
      week-02/week.yaml
      week-03/week.yaml
    skills/
    datasets/
    assessments/
```

Week files reference skill names and define what students complete per week.

## Bundled Big Data Module Content

Included in this MVP:

- 3 complete labs:
  - Lab 1: Python and CSV basics (`lab-csv-basics`)
  - Lab 2: pandas filtering and aggregation (`lab-pandas-aggregation`)
  - Lab 3: introductory distributed processing concepts (`lab-distributed-concepts`)
- 2 quizzes: `quiz-intro-data`, `quiz-pandas-core`
- 2 python-test skills: `test-task1`, `test-task2`
- 1 dataset explorer: `dataset-sales-overview`
- Hint/Q&A/review skills and sample datasets

## Lecturer Workflow

Add and ship new content without changing core code:

```bash
opencourse init-coursepack
opencourse init-week 4
opencourse init-skill skills/week4-quiz --skill-type quiz
opencourse validate-coursepack coursepacks/your-pack
```

Then publish via git tag/release and students update with pip.

## Weekly Update Strategy

Recommended workflow for weekly teaching drops:

1. Lecturer adds `week-0N` content and skills, then increments package version.
2. Lecturer publishes a new release (GitHub + PyPI).
3. Students run `python3 -m pip install --upgrade opencourse` at the start of each week.
4. Students run `opencourse week list` and `opencourse learn` to pick up new activities.

For discoverability, add a small weekly `review` skill (for example `review-week4`) that summarizes goals, required labs, and due tasks. This keeps updates visible inside the same skill workflow students already use.

## Student Workflow

- Run `opencourse learn` to see current week
- Launch activities with `quiz`, `lab`, `test`, `ask`
- Track completion with `opencourse progress`
- Resume with `opencourse continue`

Progress is stored locally in workspace file:

- `.opencourse-progress.json`

## AI vs Deterministic Checks

Deterministic built-in behavior:

- quiz grading
- pytest execution for coding checks
- skill and coursepack validation
- progress tracking

Optional AI behavior (adapter/plugin ready):

- concept Q&A
- hints
- error explanations
- Socratic tutoring

If no AI is configured, OpenCourse still works fully.

## Development

```bash
python3 -m pip install -e .
pytest
opencourse --help
```

## Project Structure

```text
src/opencourse/
  main.py
  branding.py
  config.py
  progress.py
  models.py
  ai/
  skills/
  coursepacks/
  runtimes/
  bundled/

tests/
docs/
examples/
```

## Compatibility Notes

See [docs/compatibility.md](docs/compatibility.md).
See [docs/module-spec.md](docs/module-spec.md) for external module format.
