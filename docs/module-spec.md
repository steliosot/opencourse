# OpenCourse External Module Spec (v1)

This spec enables third-party teaching modules to plug into OpenCourse while staying close to OpenClaw conventions.

## Required root file

`opencourse-module.yaml`

Example:

```yaml
id: big-data-processing
title: Big Data Processing Module
version: 0.1.0
spec_version: "1"
entry_coursepack: big-data-processing
openclaw_compatible: true
```

## Required structure

```text
<repo-root>/
  opencourse-module.yaml
  coursepacks/
    <entry_coursepack>/
      course.yaml
      weeks/
      skills/
```

## Skill compatibility requirements

Each skill must keep OpenClaw-compatible `SKILL.md` frontmatter:
- `name`
- `description`
- `module`
- `skill_type`

OpenCourse extensions:
- `week`
- `session`

## Recommended week/session organization

```text
coursepacks/<module-id>/
  weeks/
    week-01/
      week.yaml
  skills/
    s1-quiz-intro/
    s1-lab-csv/
    s2-quiz-pandas/
    s2-lab-pandas/
    s3-lab-distributed/
    s3-review/
```

## Student-facing flow

```bash
opencourse module add <git-url>
opencourse module list
opencourse set module <module-id>
opencourse set week 1
opencourse set session 1
opencourse learn
```
