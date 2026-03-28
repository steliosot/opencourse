# OpenCourse Module Template

This repository is an empty starter template for OpenCourse modules.

## Structure

- `opencourse-module.yaml`: module manifest
- `coursepacks/<module-id>/course.yaml`: course metadata
- `coursepacks/<module-id>/weeks/week-01/week.yaml`: first week scaffold (empty)
- `coursepacks/<module-id>/skills/`: add OpenClaw-style skill folders (`SKILL.md` + YAML frontmatter)
- `coursepacks/<module-id>/datasets/`: optional datasets
- `coursepacks/<module-id>/assessments/`: optional deterministic checks

## Next steps

1. Add your week/session content under `coursepacks/<module-id>`.
2. Create skills in `skills/` and reference them from `weeks/week-XX/week.yaml`.
3. Register from OpenCourse:

```bash
opencourse module add https://github.com/<your-org>/<your-module-repo>.git
```
