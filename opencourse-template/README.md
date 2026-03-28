# OpenCourse Template Module

This repository is a template for external OpenCourse modules.

## Register in OpenCourse

```bash
opencourse module add <YOUR_GIT_URL>
opencourse module list
opencourse set module big-data-processing
opencourse set week 1
opencourse set session 1
opencourse learn
```

## Required structure

- `opencourse-module.yaml`
- `coursepacks/<module-id>/course.yaml`
- `coursepacks/<module-id>/weeks/week-XX/week.yaml`
- `coursepacks/<module-id>/skills/<skill-name>/SKILL.md`
