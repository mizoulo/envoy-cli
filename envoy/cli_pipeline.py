"""CLI commands for managing and running envoy pipelines."""
from __future__ import annotations

import click
from pathlib import Path
from envoy.pipeline import PipelineManager, PipelineStep


def _manager(pipelines_dir: str) -> PipelineManager:
    return PipelineManager(Path(pipelines_dir))


@click.group("pipeline")
def pipeline_cli():
    """Create and run multi-step envoy pipelines."""


@pipeline_cli.command("define")
@click.argument("name")
@click.option("--step", "steps", multiple=True, metavar="ACTION",
              help="Add a step by action name (repeatable).")
@click.option("--dir", "pipelines_dir", default=".envoy/pipelines", show_default=True)
def define(name: str, steps: tuple, pipelines_dir: str):
    """Define a named pipeline from a list of actions."""
    if not steps:
        raise click.UsageError("Provide at least one --step.")
    mgr = _manager(pipelines_dir)
    pipeline_steps = [PipelineStep(action=s) for s in steps]
    mgr.save(name, pipeline_steps)
    click.echo(f"Pipeline '{name}' saved with {len(pipeline_steps)} step(s).")


@pipeline_cli.command("run")
@click.argument("name")
@click.option("--dir", "pipelines_dir", default=".envoy/pipelines", show_default=True)
@click.pass_context
def run(ctx: click.Context, name: str, pipelines_dir: str):
    """Run a saved pipeline."""
    mgr = _manager(pipelines_dir)

    def executor(action: str, args: dict):
        click.echo(f"  → {action}")
        # Placeholder: real implementation would dispatch to envoy subsystems
        return True, None

    result = mgr.run(name, executor)
    if result.success:
        click.echo(f"Pipeline '{name}' completed ({result.steps_run} steps).")
    else:
        click.echo(
            f"Pipeline '{name}' failed at step '{result.failed_step}': {result.error}",
            err=True,
        )
        ctx.exit(1)


@pipeline_cli.command("list")
@click.option("--dir", "pipelines_dir", default=".envoy/pipelines", show_default=True)
def list_pipelines(pipelines_dir: str):
    """List all saved pipelines."""
    mgr = _manager(pipelines_dir)
    names = mgr.list_pipelines()
    if not names:
        click.echo("No pipelines defined.")
        return
    for n in names:
        click.echo(n)


@pipeline_cli.command("delete")
@click.argument("name")
@click.option("--dir", "pipelines_dir", default=".envoy/pipelines", show_default=True)
def delete(name: str, pipelines_dir: str):
    """Delete a saved pipeline."""
    mgr = _manager(pipelines_dir)
    if mgr.delete(name):
        click.echo(f"Pipeline '{name}' deleted.")
    else:
        click.echo(f"Pipeline '{name}' not found.", err=True)
