# OpenCourse and OpenClaw Compatibility

## OpenClaw-Compatible Conventions

OpenCourse intentionally follows these conventions so skills can be reused with minimal changes:

- `SKILL.md` is the primary skill descriptor
- YAML frontmatter in `SKILL.md` is parsed and used as metadata
- skill folders live under `skills/`
- optional workspace agent skills under `./.agents/skills`
- precedence favors local workspace/user skills over bundled defaults

## OpenCourse Teaching Extensions

OpenCourse adds teaching-focused fields and conventions:

- `week` metadata for weekly delivery
- `skill_type` mapped to learning runtimes (`quiz`, `guided-lab`, `python-test`, etc.)
- coursepack-level organization (`course.yaml`, `weeks/week-*/week.yaml`)
- local learner progress tracking (`.opencourse-progress.json`)

These are extensions, not hard breaks.

## Adapting an OpenCourse Skill for OpenClaw

1. Keep `SKILL.md` frontmatter and body.
2. If OpenClaw ignores `week`/`skill_type`, leave them in place or remove optional fields.
3. Move any OpenCourse-specific runtime files (`quiz.yaml`, `qna.yaml`) to formats expected by your OpenClaw runtime.
4. Preserve folder naming and prompt files to maximize reuse.

## Adapting an OpenClaw-Style Skill into OpenCourse

1. Place skill directory in one of:
   - `./skills`
   - `./.agents/skills`
   - `~/.opencourse/skills` (or `$OPENCOURSE_HOME/skills`)
2. Ensure `SKILL.md` has YAML frontmatter with:
   - `name`
   - `description`
   - `module`
   - `skill_type`
3. Add optional `week` and runtime metadata to integrate into weekly teaching flow.
4. Validate with:

```bash
opencourse skills validate path/to/skill
```

## Compatibility Boundaries

OpenCourse aims for "close enough to reuse" compatibility, not a byte-identical runtime.

- Skill descriptor and folder conventions are aligned.
- Teaching orchestration (weeks/progress/tests) is intentionally extended.
- Deterministic grading and validation are built in for educational use.
