from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from .ai.manager import AIManager, DEFAULT_MODEL, FALLBACK_MODEL, OPTIONAL_MODEL
from .branding import banner_panel
from .coursepacks import CoursePackLoader, validate_coursepack
from .models import CoursePack, Skill
from .progress import ProgressStore
from .runtimes import RuntimeEngine
from .skills import SkillLoader

console = Console()
app = typer.Typer(help="OpenCourse CLI", add_completion=False, rich_markup_mode="rich")
skills_app = typer.Typer(help="Skill management commands")
ai_app = typer.Typer(help="AI management commands")
module_app = typer.Typer(help="Module management commands")
set_app = typer.Typer(help="Setters for OpenCourse session defaults")
app.add_typer(skills_app, name="skills")
app.add_typer(ai_app, name="ai")
app.add_typer(module_app, name="module")
app.add_typer(set_app, name="set")


class AppContext:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.coursepacks = CoursePackLoader(workspace)
        self.progress_store = ProgressStore(workspace)
        self.ai_manager = AIManager()
        self.engine = RuntimeEngine(console, ai_provider=self.ai_manager.get_provider())

    def get_pack(self, module_id: str = "big-data-processing") -> CoursePack:
        packs = self.coursepacks.discover()
        if module_id not in packs:
            raise typer.BadParameter(f"Module '{module_id}' not found. Available: {', '.join(packs.keys())}")
        return packs[module_id]

    def list_packs(self) -> dict[str, CoursePack]:
        return self.coursepacks.discover()

    def get_skills(self, pack: CoursePack) -> dict[str, Skill]:
        loader = SkillLoader(self.workspace)
        return loader.load_skills(include_coursepack=pack.path)


@app.callback(invoke_without_command=True)
def root(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand:
        return

    state = AppContext(Path.cwd())
    progress = state.progress_store.load()
    packs = state.list_packs()
    if not packs:
        console.print("[red]No course modules found. Add a coursepack first.[/red]")
        raise typer.Exit(code=1)
    if progress.module_id not in packs:
        progress.module_id = sorted(packs.keys())[0]
        progress.current_week = 1
        progress.last_skill = None
        progress.completed_skills = {}
        state.progress_store.save(progress)
    pack = packs[progress.module_id]

    console.print(banner_panel())
    table = Table(title="Available Modules", border_style="cyan")
    table.add_column("ID")
    table.add_column("Title")
    table.add_column("Weeks")
    table.add_column("Current")
    for module_id, module_pack in sorted(packs.items()):
        table.add_row(
            module_id,
            module_pack.title,
            str(len(module_pack.weeks)),
            "yes" if module_id == progress.module_id else "",
        )
    console.print(table)
    console.print(
        Panel(
            f"Current module: [cyan]{pack.title}[/cyan]\n"
            f"Current week: [bold]{progress.current_week}[/bold]\n"
            "Use [bold]opencourse set module <id>[/bold] to switch modules.\n"
            "Use [bold]opencourse learn[/bold] to continue.",
            border_style="cyan",
            title="Session",
        )
    )


@app.command()
def learn() -> None:
    """Show current week skills and suggest the next activity."""
    state = AppContext(Path.cwd())
    progress = state.progress_store.load()
    pack = state.get_pack(progress.module_id)
    skills = state.get_skills(pack)

    week = next((w for w in pack.weeks if w.week == progress.current_week), None)
    if week is None:
        raise typer.Exit(code=1)

    table = Table(title=f"Week {week.week}: {week.title}", border_style="cyan")
    table.add_column("Skill")
    table.add_column("Type")
    table.add_column("Status")

    for skill_name in week.skills:
        skill = skills.get(skill_name)
        if skill is None:
            continue
        status = "done" if skill_name in progress.completed_skills else "pending"
        table.add_row(skill_name, skill.metadata.skill_type, status)

    console.print(table)


@app.command()
def practice() -> None:
    """List incomplete skills for the current week."""
    state = AppContext(Path.cwd())
    progress = state.progress_store.load()
    pack = state.get_pack(progress.module_id)

    week = next((w for w in pack.weeks if w.week == progress.current_week), None)
    if week is None:
        raise typer.Exit(code=1)

    pending = [s for s in week.skills if s not in progress.completed_skills]
    if not pending:
        console.print("[green]All skills complete for this week.[/green]")
        return
    console.print("[bold cyan]Pending skills:[/bold cyan]")
    for skill_name in pending:
        console.print(f"- {skill_name}")


@app.command()
def validate() -> None:
    """Validate the currently selected coursepack."""
    state = AppContext(Path.cwd())
    progress = state.progress_store.load()
    pack = state.get_pack(progress.module_id)
    valid, errors = validate_coursepack(pack.path)
    if valid:
        console.print("[green]Coursepack is valid.[/green]")
        return
    console.print("[red]Validation errors:[/red]")
    for err in errors:
        console.print(f"- {err}")
    raise typer.Exit(code=1)


@app.command("setup-ai")
def setup_ai() -> None:
    manager = AIManager()
    console.print("[bold cyan]OpenCourse AI setup[/bold cyan]")
    os_name = manager.detect_os()
    console.print(f"[green]✔[/green] OS detected: {os_name}")

    if not manager.ollama_installed():
        console.print("[yellow]Ollama not found on this system.[/yellow]")
        console.print("Install Ollama from: https://ollama.com/download")
        Prompt.ask("Press Enter after installing Ollama")
        if not manager.ollama_installed():
            console.print("[red]Ollama is still not detected. Run `opencourse setup-ai` again after install.[/red]")
            raise typer.Exit(code=1)
    console.print("[green]✔[/green] Ollama detected")

    endpoint = "http://localhost:11434"
    if not manager.endpoint_ok(endpoint):
        console.print("[yellow]Ollama endpoint is not responding at http://localhost:11434[/yellow]")
        console.print("Start Ollama, then retry connection.")
        retry = Confirm.ask("Retry endpoint check now?", default=True)
        if retry and not manager.endpoint_ok(endpoint):
            console.print("[red]Connection still failing. Run `opencourse ai status` after starting Ollama.[/red]")
            raise typer.Exit(code=1)
        if not retry:
            raise typer.Exit(code=1)
    console.print("[green]✔[/green] Ollama endpoint reachable")

    selected_model = DEFAULT_MODEL
    ok, message = manager.ensure_model(selected_model)
    if not ok:
        console.print(f"[yellow]{message}[/yellow]")
        console.print(f"[yellow]Trying fallback model {FALLBACK_MODEL}[/yellow]")
        selected_model = FALLBACK_MODEL
        ok, message = manager.ensure_model(selected_model)
        if not ok:
            console.print(f"[red]{message}[/red]")
            raise typer.Exit(code=1)
    console.print(f"[green]✔[/green] {message}")
    console.print(f"[bright_black]Optional model available: {OPTIONAL_MODEL}[/bright_black]")

    manager.enable_ollama(model=selected_model, endpoint=endpoint)
    test_ok, response = manager.test_inference("Say hello in one sentence.")
    if not test_ok:
        console.print(f"[red]AI test failed:[/red] {response}")
        raise typer.Exit(code=1)
    console.print("[green]✔[/green] Connection OK")
    console.print(Panel(response, title="AI Test Response", border_style="cyan"))
    console.print("[bold green]AI enabled[/bold green]")
    console.print(f"Config saved: {manager.config_path}")


@ai_app.command("status")
def ai_status() -> None:
    manager = AIManager()
    status = manager.status()
    table = Table(title="AI Status", border_style="cyan")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Enabled", status["enabled"])
    table.add_row("Provider", status["provider"])
    table.add_row("Model", status["model"])
    table.add_row("Endpoint", status["endpoint"])
    table.add_row("Connection", status["connection"])
    table.add_row("Ollama installed", status["ollama_installed"])
    console.print(table)


@ai_app.command("test")
def ai_test() -> None:
    manager = AIManager()
    ok, response = manager.test_inference("Say hello in one sentence.")
    if not ok:
        console.print(f"[red]AI test failed:[/red] {response}")
        raise typer.Exit(code=1)
    console.print("[green]AI test passed[/green]")
    console.print(Panel(response, title="AI Output", border_style="cyan"))


@ai_app.command("disable")
def ai_disable() -> None:
    manager = AIManager()
    path = manager.disable_ai()
    console.print(f"[yellow]AI disabled[/yellow] ({path})")


@ai_app.command("use")
def ai_use(model: str) -> None:
    manager = AIManager()
    if not manager.ollama_installed():
        console.print("[red]Ollama is not installed. Install first: https://ollama.com/download[/red]")
        raise typer.Exit(code=1)
    if not manager.endpoint_ok():
        console.print("[red]Ollama endpoint is not reachable. Start Ollama and retry.[/red]")
        raise typer.Exit(code=1)
    ok, message = manager.ensure_model(model)
    if not ok:
        console.print(f"[red]{message}[/red]")
        raise typer.Exit(code=1)
    path = manager.use_model(model)
    console.print(f"[green]✔[/green] {message}")
    console.print(f"[green]AI model set to {model}[/green] ({path})")


@module_app.command("list")
def module_list() -> None:
    state = AppContext(Path.cwd())
    progress = state.progress_store.load()
    packs = state.list_packs()
    table = Table(title="Modules", border_style="cyan")
    table.add_column("ID")
    table.add_column("Title")
    table.add_column("Weeks")
    table.add_column("Current")
    for module_id, pack in sorted(packs.items()):
        table.add_row(
            module_id,
            pack.title,
            str(len(pack.weeks)),
            "yes" if module_id == progress.module_id else "",
        )
    console.print(table)


def _set_module(module_id: str) -> None:
    state = AppContext(Path.cwd())
    progress = state.progress_store.load()
    packs = state.list_packs()
    if module_id not in packs:
        console.print(f"[red]Unknown module:[/red] {module_id}")
        if packs:
            console.print("Available modules:")
            for key in sorted(packs.keys()):
                console.print(f"- {key}")
        raise typer.Exit(code=1)
    progress.module_id = module_id
    progress.current_week = 1
    progress.last_skill = None
    progress.completed_skills = {}
    state.progress_store.save(progress)
    console.print(f"[green]Module set to {module_id}[/green]")
    console.print("Run [bold]opencourse learn[/bold] to start.")


@module_app.command("set")
def module_set(module_id: str) -> None:
    _set_module(module_id)


@module_app.command("current")
def module_current() -> None:
    state = AppContext(Path.cwd())
    progress = state.progress_store.load()
    pack = state.get_pack(progress.module_id)
    console.print(
        Panel(
            f"ID: {pack.id}\nTitle: {pack.title}\nCurrent week: {progress.current_week}",
            title="Current Module",
            border_style="cyan",
        )
    )


@set_app.command("module")
def set_module_alias(module_id: str) -> None:
    _set_module(module_id)


@skills_app.command("list")
def skills_list() -> None:
    """List all discovered skills with source precedence."""
    state = AppContext(Path.cwd())
    progress = state.progress_store.load()
    pack = state.get_pack(progress.module_id)
    skills = state.get_skills(pack)

    table = Table(title="Available Skills", border_style="cyan")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Week")
    table.add_column("Source")
    table.add_column("Enabled")

    for name in sorted(skills):
        skill = skills[name]
        table.add_row(
            name,
            skill.metadata.skill_type,
            str(skill.metadata.week or "-"),
            skill.source,
            "yes" if skill.enabled else "no",
        )
    console.print(table)


@skills_app.command("show")
def skills_show(name: str) -> None:
    """Show metadata and details for one skill."""
    state = AppContext(Path.cwd())
    progress = state.progress_store.load()
    pack = state.get_pack(progress.module_id)
    skills = state.get_skills(pack)
    skill = skills.get(name)
    if not skill:
        console.print(f"[red]Skill not found:[/red] {name}")
        raise typer.Exit(code=1)

    console.print(
        Panel(
            f"Name: {skill.metadata.name}\n"
            f"Description: {skill.metadata.description}\n"
            f"Type: {skill.metadata.skill_type}\n"
            f"Module: {skill.metadata.module}\n"
            f"Week: {skill.metadata.week}\n"
            f"Version: {skill.metadata.version}\n"
            f"Source: {skill.source}\n"
            f"Path: {skill.path}",
            border_style="cyan",
            title="Skill Details",
        )
    )


@skills_app.command("enable")
def skills_enable(name: str) -> None:
    loader = SkillLoader(Path.cwd())
    loader.enable_skill(name)
    console.print(f"[green]Enabled skill:[/green] {name}")


@skills_app.command("disable")
def skills_disable(name: str) -> None:
    loader = SkillLoader(Path.cwd())
    loader.disable_skill(name)
    console.print(f"[yellow]Disabled skill:[/yellow] {name}")


@skills_app.command("validate")
def skills_validate(path: Path) -> None:
    errors = SkillLoader.validate_skill_dir(path)
    if not errors:
        console.print("[green]Skill directory valid[/green]")
        return
    console.print("[red]Skill directory invalid[/red]")
    for error in errors:
        console.print(f"- {error}")
    raise typer.Exit(code=1)


def week_list() -> None:
    state = AppContext(Path.cwd())
    progress = state.progress_store.load()
    pack = state.get_pack(progress.module_id)

    table = Table(title="Course Weeks", border_style="cyan")
    table.add_column("Week")
    table.add_column("Title")
    table.add_column("Skills")
    table.add_column("Current")

    for week in pack.weeks:
        table.add_row(
            str(week.week),
            week.title,
            str(len(week.skills)),
            "yes" if week.week == progress.current_week else "",
        )
    console.print(table)


def week_open(number: int) -> None:
    state = AppContext(Path.cwd())
    progress = state.progress_store.load()
    pack = state.get_pack(progress.module_id)
    week = next((w for w in pack.weeks if w.week == number), None)
    if not week:
        console.print(f"[red]Week {number} not found[/red]")
        raise typer.Exit(code=1)

    console.print(Panel(f"{week.title}\n\n{week.summary}", title=f"Week {number}", border_style="cyan"))
    console.print("Skills:")
    for s in week.skills:
        console.print(f"- {s}")


def week_start(number: int) -> None:
    state = AppContext(Path.cwd())
    progress = state.progress_store.load()
    progress.current_week = number
    state.progress_store.save(progress)
    console.print(f"[green]Current week set to {number}[/green]")


@app.command("week")
def week_command(
    action: str | None = typer.Argument(default=None),
    value: str | None = typer.Argument(default=None),
) -> None:
    """
    Manage weekly flow.

    Examples:
    - opencourse week list
    - opencourse week open 1
    - opencourse week start 2
    - opencourse week 1
    """
    if action is None:
        week_list()
        return

    if action.isdigit() and value is None:
        week_start(int(action))
        return

    if action == "list" and value is None:
        week_list()
        return

    if action == "open" and value and value.isdigit():
        week_open(int(value))
        return

    if action == "start" and value and value.isdigit():
        week_start(int(value))
        return

    console.print("[red]Invalid week command. Try:[/red] week list | week open <n> | week start <n> | week <n>")
    raise typer.Exit(code=2)


@app.command("continue")
def continue_learning() -> None:
    state = AppContext(Path.cwd())
    progress = state.progress_store.load()
    pack = state.get_pack(progress.module_id)
    skills = state.get_skills(pack)

    if progress.last_skill and progress.last_skill in skills:
        skill = skills[progress.last_skill]
        console.print(f"Continuing with last skill: [cyan]{progress.last_skill}[/cyan]")
        state.engine.run_skill(skill, pack, progress)
        state.progress_store.save(progress)
        return

    week = next((w for w in pack.weeks if w.week == progress.current_week), None)
    if not week:
        raise typer.Exit(code=1)
    pending = [s for s in week.skills if s not in progress.completed_skills and s in skills]
    if not pending:
        console.print("[green]Nothing pending. Try `opencourse week start <n>`[/green]")
        return

    skill = skills[pending[0]]
    console.print(f"Launching next pending skill: [cyan]{skill.metadata.name}[/cyan]")
    state.engine.run_skill(skill, pack, progress)
    state.progress_store.save(progress)


def _launch_skill(name: str, expected_type: str | None = None) -> None:
    state = AppContext(Path.cwd())
    progress = state.progress_store.load()
    pack = state.get_pack(progress.module_id)
    skills = state.get_skills(pack)
    skill = skills.get(name)
    if not skill:
        console.print(f"[red]Skill not found:[/red] {name}")
        raise typer.Exit(code=1)
    if expected_type and skill.metadata.skill_type != expected_type:
        console.print(
            f"[red]Skill '{name}' is type '{skill.metadata.skill_type}', expected '{expected_type}'.[/red]"
        )
        raise typer.Exit(code=1)
    state.engine.run_skill(skill, pack, progress)
    state.progress_store.save(progress)


@app.command()
def lab(name: str) -> None:
    _launch_skill(name, expected_type="guided-lab")


@app.command()
def quiz(name: str) -> None:
    _launch_skill(name, expected_type="quiz")


@app.command("test")
def python_test(name: str) -> None:
    _launch_skill(name, expected_type="python-test")


@app.command("explain-error")
def explain_error(name: str) -> None:
    _launch_skill(name, expected_type="explain-error")


@app.command()
def ask(question: str | None = None) -> None:
    state = AppContext(Path.cwd())
    q = question or Prompt.ask("Ask OpenCourse")
    answer = state.engine.ask_ai(q)
    console.print(Panel(answer, title="OpenCourse Ask", border_style="cyan"))


@app.command()
def progress() -> None:
    state = AppContext(Path.cwd())
    p = state.progress_store.load()
    pack = state.get_pack(p.module_id)

    table = Table(title="Progress", border_style="cyan")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Module", p.module_id)
    table.add_row("Current week", str(p.current_week))
    table.add_row("Completed skills", str(len(p.completed_skills)))
    table.add_row("Last skill", p.last_skill or "-")
    console.print(table)

    week = next((w for w in pack.weeks if w.week == p.current_week), None)
    if week:
        remaining = [s for s in week.skills if s not in p.completed_skills]
        if remaining:
            console.print("[bold cyan]Remaining this week:[/bold cyan]")
            for s in remaining:
                console.print(f"- {s}")


@app.command()
def update() -> None:
    console.print(
        "Install via pip: [bold]python3 -m pip install opencourse[/bold]\n"
        "Update via pip: [bold]python3 -m pip install --upgrade opencourse[/bold]\n"
        "If installed from source: [bold]git pull && python3 -m pip install -e .[/bold]"
    )


@app.command("init-skill")
def init_skill(path: Path = Path("skills/new-skill"), skill_type: str = "guided-lab") -> None:
    path.mkdir(parents=True, exist_ok=True)
    skill_md = path / "SKILL.md"
    if skill_md.exists():
        console.print(f"[yellow]Skill already exists:[/yellow] {path}")
        return

    skill_md.write_text(
        "---\n"
        f"name: {path.name}\n"
        "description: New OpenCourse skill\n"
        "version: 0.1.0\n"
        "tags: [teaching]\n"
        "module: big-data-processing\n"
        "week: 1\n"
        f"skill_type: {skill_type}\n"
        "runtime: {}\n"
        "---\n\n"
        "# Skill\n\n"
        "Describe the learner task here.\n",
        encoding="utf-8",
    )
    (path / "prompts").mkdir(exist_ok=True)
    (path / "prompts" / "instructions.md").write_text("# Instructions\n", encoding="utf-8")
    console.print(f"[green]Created skill scaffold:[/green] {path}")


@app.command("init-week")
def init_week(number: int, coursepack_path: Path = Path("coursepacks/big-data-processing")) -> None:
    week_dir = coursepack_path / "weeks" / f"week-{number:02d}"
    week_dir.mkdir(parents=True, exist_ok=True)
    week_file = week_dir / "week.yaml"
    if week_file.exists():
        console.print(f"[yellow]Week already exists:[/yellow] {week_file}")
        return
    week_file.write_text(
        "week: {0}\n"
        "title: Week {0}\n"
        "summary: Add learning goals for this week.\n"
        "skills:\n"
        "  - example-skill\n".format(number),
        encoding="utf-8",
    )
    console.print(f"[green]Created week scaffold:[/green] {week_file}")


@app.command("init-coursepack")
def init_coursepack(path: Path = Path("coursepacks/new-course")) -> None:
    (path / "weeks" / "week-01").mkdir(parents=True, exist_ok=True)
    (path / "skills").mkdir(parents=True, exist_ok=True)
    (path / "datasets").mkdir(parents=True, exist_ok=True)
    (path / "assessments").mkdir(parents=True, exist_ok=True)

    (path / "course.yaml").write_text(
        "id: new-course\n"
        "title: New Course\n"
        "description: Describe this coursepack\n"
        "module: new-course\n"
        "version: 0.1.0\n",
        encoding="utf-8",
    )
    (path / "weeks" / "week-01" / "week.yaml").write_text(
        "week: 1\n"
        "title: Week 1\n"
        "summary: Getting started\n"
        "skills:\n"
        "  - intro-quiz\n",
        encoding="utf-8",
    )
    console.print(f"[green]Created coursepack scaffold:[/green] {path}")


@app.command("validate-coursepack")
def validate_coursepack_cmd(path: Path) -> None:
    valid, errors = validate_coursepack(path)
    if valid:
        console.print("[green]Coursepack valid[/green]")
        return
    console.print("[red]Coursepack invalid[/red]")
    for e in errors:
        console.print(f"- {e}")
    raise typer.Exit(code=1)


def run() -> None:
    app()


if __name__ == "__main__":
    run()
