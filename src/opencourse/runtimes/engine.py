from __future__ import annotations

import csv
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from ..ai.base import AIProvider
from ..ai.disabled import DisabledAIProvider
from ..ai.rag import retrieve_context
from ..models import CoursePack, ProgressState, Skill


class RuntimeEngine:
    def __init__(
        self,
        console: Console,
        ai_provider: AIProvider | None = None,
        workspace_root: Path | None = None,
    ) -> None:
        self.console = console
        self.ai = ai_provider or DisabledAIProvider()
        self.workspace_root = workspace_root or Path.cwd()

    def run_skill(
        self,
        skill: Skill,
        pack: CoursePack,
        progress: ProgressState,
        *,
        show_solution: bool = False,
    ) -> bool:
        skill_type = skill.metadata.skill_type
        if skill_type == "quiz":
            return self._run_quiz(skill, progress)
        if skill_type == "guided-lab":
            return self._run_lab(skill, pack, progress, show_solution=show_solution)
        if skill_type == "python-test":
            return self._run_python_test(skill, progress)
        if skill_type == "dataset-explorer":
            return self._run_dataset_explorer(skill, pack, progress)
        if skill_type == "hint":
            return self._run_hint(skill)
        if skill_type == "review":
            return self._run_review(skill, pack, progress)
        if skill_type == "qna":
            return self._run_qna(skill)
        if skill_type == "explain-error":
            return self._run_explain_error(skill)

        self.console.print(f"[red]Unsupported skill type:[/red] {skill_type}")
        return False

    def ask_ai(self, question: str) -> str:
        context = retrieve_context(question, self.workspace_root)
        if context:
            prompt = (
                "Answer the student's question using the provided local course/workspace context when relevant. "
                "If context is insufficient, say what is missing briefly.\n\n"
                f"Question:\n{question}\n\n"
                f"Context:\n{context}"
            )
            return self.ai.generate(prompt)
        return self.ai.generate(question)

    def _run_quiz(self, skill: Skill, progress: ProgressState) -> bool:
        quiz_file = skill.path / "quiz.yaml"
        if not quiz_file.exists():
            self.console.print("[red]quiz.yaml missing for this skill[/red]")
            return False
        quiz = yaml.safe_load(quiz_file.read_text(encoding="utf-8"))
        questions = quiz.get("questions", [])
        score = 0
        total = len(questions)
        attempts: list[dict[str, str | int | bool]] = []

        self.console.print(Panel.fit(f"Quiz: {skill.metadata.name}", border_style="cyan"))
        for idx, q in enumerate(questions, start=1):
            self.console.print(f"\n[bold]{idx}. {q['question']}[/bold]")
            options = q.get("options", [])
            answer = self._select_answer(options)
            correct = str(q.get("answer", "")).strip()
            selected_value = answer
            if answer.isdigit():
                selected_index = int(answer) - 1
                if 0 <= selected_index < len(options):
                    selected_value = str(options[selected_index]).strip()
            is_correct = selected_value.lower() == correct.lower()
            if is_correct:
                self.console.print("[green]Correct[/green]")
                score += 1
            else:
                self.console.print(f"[yellow]Not quite. Correct answer:[/yellow] {correct}")
            attempts.append(
                {
                    "question_number": idx,
                    "question": q["question"],
                    "answer_raw": answer,
                    "answer_resolved": selected_value,
                    "correct_answer": correct,
                    "is_correct": is_correct,
                }
            )

        self.console.print(f"\n[bold cyan]Score:[/bold cyan] {score}/{total}")
        should_save = Prompt.ask(
            "Would you like to save your quiz answers and results to a file? (y/n)",
            default="n",
        ).strip().lower()
        if should_save in {"y", "yes"}:
            output_dir = Path.cwd() / "quiz-results"
            output_dir.mkdir(parents=True, exist_ok=True)
            filename = f"{skill.metadata.name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.yaml"
            output_path = output_dir / filename
            payload = {
                "quiz": skill.metadata.name,
                "module": skill.metadata.module,
                "week": skill.metadata.week,
                "score": {"correct": score, "total": total},
                "saved_at": datetime.now().isoformat(timespec="seconds"),
                "attempts": attempts,
            }
            output_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
            self.console.print(f"[green]Saved quiz results:[/green] {output_path}")
        if score == total:
            progress.mark_complete(skill.metadata.name)
            return True
        return False

    def _select_answer(self, options: list[str]) -> str:
        if not options:
            return Prompt.ask("Your answer").strip()
        try:
            import questionary

            labels = [f"{i + 1}. {opt}" for i, opt in enumerate(options)]
            selected = questionary.select(
                "Choose an answer (up/down + Enter)",
                choices=labels,
                qmark="",
            ).ask()
            if not selected:
                return Prompt.ask("Your answer").strip()
            return selected.split(". ", 1)[1].strip()
        except Exception:  # noqa: BLE001
            for opt_idx, opt in enumerate(options, start=1):
                self.console.print(f"  {opt_idx}. {opt}")
            return Prompt.ask("Your answer").strip()

    def _run_lab(
        self,
        skill: Skill,
        pack: CoursePack,
        progress: ProgressState,
        *,
        show_solution: bool = False,
    ) -> bool:
        instruction_file = skill.path / "prompts" / "instructions.md"
        if not instruction_file.exists():
            self.console.print("[red]Lab instructions missing at prompts/instructions.md[/red]")
            return False

        self.console.print(Panel.fit(f"Lab: {skill.metadata.name}", border_style="cyan"))
        self.console.print(instruction_file.read_text(encoding="utf-8"))
        if skill.metadata.name == "lab-csv-basics":
            lab_dir = self._bootstrap_csv_lab_workspace(pack, skill, progress)
            self.console.print("[green]Lab scaffold created.[/green]")
            self.console.print(
                Panel(
                    f"Module: {pack.title}\n"
                    f"Lab: {skill.metadata.name}\n\n"
                    "Lab workspace ready.\n"
                    f"Folder: {lab_dir}\n"
                    f"Dataset copied: {lab_dir / 'data' / 'sales.csv'}\n"
                    f"Starter file: {lab_dir / 'exercise.py'}\n"
                    f"Tests: {lab_dir / 'tests' / 'test_exercise.py'}",
                    title="Scaffold Complete",
                    border_style="cyan",
                )
            )
            self.console.print("[bold cyan]Next steps:[/bold cyan]")
            self.console.print(f"1. Open [bold]{lab_dir / 'exercise.py'}[/bold]")
            self.console.print("2. Implement `revenue_by_region(rows)`")
            self.console.print(f"3. Run [bold]python -m pytest {lab_dir / 'tests'} -q[/bold]")
            self.console.print(
                "[bold cyan]Run this test command:[/bold cyan]\n"
                f"  [bold]python -m pytest {lab_dir / 'tests'} -q[/bold]"
            )
            if show_solution:
                self._show_lab_solution(skill=skill, pack=pack)
            run_now = Prompt.ask("Run the tests now? (y/n)", default="y").strip().lower()
            if run_now in {"y", "yes"}:
                ok = self._run_bootstrapped_lab_tests(lab_dir)
                if ok:
                    self.console.print("[green]All lab checks passed. Lab marked as done.[/green]")
                    progress.mark_complete(skill.metadata.name)
                    return True
                self.console.print(
                    "[yellow]Tests are not passing yet. Complete TODOs in exercise.py and run tests again.[/yellow]"
                )
                return False
            self.console.print("[yellow]Lab scaffold created. Run tests when ready to complete this lab.[/yellow]")
            return False

        if show_solution:
            self._show_lab_solution(skill=skill, pack=pack)
        complete = Prompt.ask("Mark this lab as complete? (y/n)", default="n")
        if complete.lower() in {"y", "yes"}:
            progress.mark_complete(skill.metadata.name)
            return True
        return False

    def _bootstrap_csv_lab_workspace(self, pack: CoursePack, skill: Skill, progress: ProgressState) -> Path:
        module_id = pack.id
        week = skill.metadata.week or progress.current_week or 1
        session = skill.metadata.session or progress.current_session or 1
        workspace_root = (
            Path.cwd()
            / "opencourse-workspace"
            / module_id
            / f"week-{week:02d}"
            / f"session-{session:02d}"
        )
        lab_dir = workspace_root / skill.metadata.name
        data_dir = lab_dir / "data"
        tests_dir = lab_dir / "tests"
        lab_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)
        tests_dir.mkdir(parents=True, exist_ok=True)

        source_csv = pack.path / "datasets" / "sales.csv"
        target_csv = data_dir / "sales.csv"
        if source_csv.exists():
            shutil.copy2(source_csv, target_csv)

        starter_file = lab_dir / "exercise.py"
        if not starter_file.exists():
            starter_file.write_text(
                "from __future__ import annotations\n\n"
                "import csv\n"
                "from pathlib import Path\n\n"
                "def load_sales(path: str | Path) -> list[dict[str, str]]:\n"
                "    with open(path, \"r\", encoding=\"utf-8\") as f:\n"
                "        return list(csv.DictReader(f))\n\n"
                "def total_units(rows: list[dict[str, str]]) -> int:\n"
                "    return sum(int(row[\"units\"]) for row in rows)\n\n"
                "def revenue_by_region(rows: list[dict[str, str]]) -> dict[str, float]:\n"
                "    # TODO: implement this function\n"
                "    raise NotImplementedError(\"Implement revenue_by_region\")\n",
                encoding="utf-8",
            )

        tests_file = tests_dir / "test_exercise.py"
        if not tests_file.exists():
            tests_file.write_text(
                "from __future__ import annotations\n\n"
                "from pathlib import Path\n\n"
                "from exercise import load_sales, total_units, revenue_by_region\n\n"
                "def test_load_and_total_units() -> None:\n"
                "    csv_path = Path(__file__).resolve().parents[1] / \"data\" / \"sales.csv\"\n"
                "    rows = load_sales(csv_path)\n"
                "    assert len(rows) > 0\n"
                "    assert total_units(rows) == 72\n\n"
                "def test_revenue_by_region() -> None:\n"
                "    rows = [\n"
                "        {\"region\": \"North\", \"units\": \"2\", \"unit_price\": \"10.0\"},\n"
                "        {\"region\": \"North\", \"units\": \"1\", \"unit_price\": \"5.0\"},\n"
                "        {\"region\": \"South\", \"units\": \"3\", \"unit_price\": \"2.5\"},\n"
                "    ]\n"
                "    result = revenue_by_region(rows)\n"
                "    assert result[\"North\"] == 25.0\n"
                "    assert result[\"South\"] == 7.5\n",
                encoding="utf-8",
            )
        return lab_dir

    def _run_bootstrapped_lab_tests(self, lab_dir: Path) -> bool:
        cmd = [sys.executable, "-m", "pytest", str(lab_dir / "tests"), "-q"]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=lab_dir)
        if result.stdout:
            self.console.print(result.stdout)
        if result.stderr:
            self.console.print(result.stderr, style="red")
        return result.returncode == 0

    def _show_lab_solution(self, *, skill: Skill, pack: CoursePack) -> None:
        solution_map = {
            "lab-csv-basics": pack.path / "assessments" / "task1" / "solution.py",
            "lab-pandas-aggregation": pack.path / "assessments" / "task2" / "solution.py",
        }
        solution_file = solution_map.get(skill.metadata.name)
        if solution_file is None or not solution_file.exists():
            self.console.print("[yellow]No reference solution is available for this lab.[/yellow]")
            return
        self.console.print(f"[cyan]Reference solution:[/cyan] {solution_file}")
        self.console.print(
            Panel(
                solution_file.read_text(encoding="utf-8"),
                title=f"Solution: {skill.metadata.name}",
                border_style="magenta",
            )
        )

    def _run_python_test(self, skill: Skill, progress: ProgressState) -> bool:
        tests_dir = skill.path / "tests"
        if not tests_dir.exists():
            self.console.print("[red]No tests/ directory found for this python-test skill[/red]")
            return False

        self.console.print(Panel.fit(f"Running Python checks: {skill.metadata.name}", border_style="cyan"))
        cmd = [sys.executable, "-m", "pytest", str(tests_dir), "-q"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.stdout:
            self.console.print(result.stdout)
        if result.stderr:
            self.console.print(result.stderr, style="red")

        if result.returncode == 0:
            self.console.print("[green]All checks passed[/green]")
            progress.mark_complete(skill.metadata.name)
            return True
        self.console.print("[yellow]Checks did not pass yet[/yellow]")
        return False

    def _run_dataset_explorer(self, skill: Skill, pack: CoursePack, progress: ProgressState) -> bool:
        cfg_file = skill.path / "skill.yaml"
        dataset_rel = None
        if cfg_file.exists():
            cfg = yaml.safe_load(cfg_file.read_text(encoding="utf-8")) or {}
            dataset_rel = cfg.get("dataset")
        if not dataset_rel:
            self.console.print("[red]skill.yaml dataset path missing[/red]")
            return False

        dataset = pack.path / dataset_rel
        if not dataset.exists():
            self.console.print(f"[red]Dataset not found:[/red] {dataset}")
            return False

        self.console.print(Panel.fit(f"Dataset Explorer: {dataset.name}", border_style="cyan"))
        with dataset.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            columns = reader.fieldnames or []

        self.console.print(f"Rows: {len(rows)}")
        self.console.print(f"Columns: {', '.join(columns)}")

        table = Table(title="Sample Rows", show_lines=False)
        for col in columns:
            table.add_column(col)
        for row in rows[:5]:
            table.add_row(*[str(row.get(col, "")) for col in columns])
        self.console.print(table)

        progress.mark_complete(skill.metadata.name)
        return True

    def _run_hint(self, skill: Skill) -> bool:
        hint_file = skill.path / "prompts" / "hint.md"
        hint_text = ""
        if not hint_file.exists():
            self.console.print("[yellow]No hint.md found for this skill[/yellow]")
        else:
            hint_text = hint_file.read_text(encoding="utf-8")
            self.console.print(Panel(hint_text, title="Hint", border_style="yellow"))
        ai_hint = self.ask_ai(
            "You are a teaching assistant for Big Data Processing.\n"
            f"Skill: {skill.metadata.name}\n"
            f"Static hint/context:\n{hint_text}\n"
            "Give one concise additional hint for a student."
        )
        self.console.print(Panel(ai_hint, title="AI Hint", border_style="cyan"))
        return True

    def _run_review(self, skill: Skill, pack: CoursePack, progress: ProgressState) -> bool:
        current_week = next((w for w in pack.weeks if w.week == progress.current_week), None)
        if current_week is None:
            self.console.print("[red]Current week not found in coursepack[/red]")
            return False
        table = Table(title=f"Week {current_week.week} Review", border_style="cyan")
        table.add_column("Skill")
        table.add_column("Status")
        for skill_name in current_week.skills:
            status = "done" if skill_name in progress.completed_skills else "pending"
            style = "green" if status == "done" else "yellow"
            table.add_row(skill_name, f"[{style}]{status}[/{style}]")
        self.console.print(table)
        completed = [s for s in current_week.skills if s in progress.completed_skills]
        pending = [s for s in current_week.skills if s not in progress.completed_skills]
        ai_review = self.ask_ai(
            "You are a supportive university tutor.\n"
            f"Week: {current_week.week} - {current_week.title}\n"
            f"Completed: {', '.join(completed) or 'none'}\n"
            f"Pending: {', '.join(pending) or 'none'}\n"
            "Provide a short progress review and suggest next step."
        )
        self.console.print(Panel(ai_review, title="AI Review", border_style="cyan"))
        progress.mark_complete(skill.metadata.name)
        return True

    def _run_qna(self, skill: Skill) -> bool:
        faq_file = skill.path / "qna.yaml"
        if faq_file.exists():
            faq = yaml.safe_load(faq_file.read_text(encoding="utf-8")) or {}
            entries = faq.get("entries", [])
            self.console.print(Panel.fit(f"Q&A: {skill.metadata.name}", border_style="cyan"))
            for item in entries:
                self.console.print(f"[bold]Q:[/bold] {item.get('q', '')}")
                self.console.print(f"A: {item.get('a', '')}\n")
            return True
        question = Prompt.ask("Ask your question")
        answer = self.ask_ai(question)
        self.console.print(Panel(answer, title="OpenCourse Assistant", border_style="cyan"))
        return True

    def _run_explain_error(self, skill: Skill) -> bool:
        self.console.print(Panel.fit(f"Explain Error: {skill.metadata.name}", border_style="cyan"))
        error_text = Prompt.ask("Paste the error or traceback")
        explanation = self.ask_ai(
            "Explain this Python/data-processing error for a student in simple steps "
            "and suggest one fix:\n"
            f"{error_text}"
        )
        self.console.print(Panel(explanation, title="AI Explain Error", border_style="cyan"))
        return True
