import click

from Canvas import Canvas


@click.group()
@click.option('-s', '--settings', 'settings_file', prompt=True, type=click.File())
@click.pass_context
def cli(ctx, settings_file):
    ctx.obj = {'canvas': Canvas.from_file(settings_file)}


@click.command("clear-weights")
@click.pass_context
def clear_wights(ctx):
    canvas = ctx.obj['canvas']
    canvas.clear_assignment_weights()


@click.command("assign-weights")
@click.pass_context
def calculate_weights(ctx):
    canvas = ctx.obj['canvas']
    canvas.assign_weights()


cli.add_command(clear_wights)
cli.add_command(calculate_weights)