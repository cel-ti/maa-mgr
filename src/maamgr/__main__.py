import os
import pprint
import time
import click
import logging
import sys
from .core import MaaInstance, create
from .utils import check_scoop, check_maa_update, redirect_stdout
from zuu.app.scoop import get_path

@click.group(invoke_without_command=True)
@click.pass_context
@click.option("--name", help="the name of the app")
@click.option("--path", help="the path of the app")
@click.option("-sc", "--skip-check", help="skip the check of the app", is_flag=True)
@click.option("-su", "--skip-update", help="skip the update of the app", is_flag=True)
@click.option("-d", "--debug", help="enable debug mode", is_flag=True)
@click.option("-v", "--verbose", help="enable verbose mode", is_flag=True)
@click.option("-l", "--log-file", help="the file to log to")
def _cli(ctx, name, path, skip_check, skip_update, debug, verbose, log_file):
    # if nothing is specified, then show the help
    if not name and not path and not skip_check and not skip_update and not debug and not verbose and not log_file:
        click.echo(_cli.get_help(ctx))
        return

    if log_file:
        if not os.path.isfile(log_file):
            open(log_file, 'w').close()
        redirect_stdout(log_file)

    if debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)
    elif verbose:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)

    flag = False
    try:
        scoop_path = get_path()
        if time.time() - os.path.getmtime(scoop_path) < 3 * 60 * 60:
            logging.info("Scoop path is less than 3 hours old. Skipping update.") 
        else:
            flag= True
    except Exception:
        flag = True

    if flag and not skip_check:
        check_scoop(echo=logging.info)
        if not skip_update:
            check_maa_update(echo=logging.info)

    instance = create(name, path)
    ctx.obj = instance
    ctx.ensure_object(MaaInstance)
    logging.info(f"set name: {name}, path: {path or "<scoop resolved>"}")

@_cli.command("export")
@click.option("-nf", "--no-file", help="do not export to file", is_flag=True)
@click.option("-p", "--path", help="the path to export to")
@click.pass_context
def export(ctx, no_file, path):
    instance : MaaInstance = ctx.obj
    res = instance.export(path, not no_file)
    if res:
        click.echo(pprint.pformat(res, indent=2))

@_cli.command("import")
@click.option("-p", "--path", help="the path to import from")
@click.option("-lb", "--latest-bkup", help="use the latest backup", is_flag=True)
@click.option("-i", "--interactive", help="interactive mode", is_flag=True)
@click.option("-k", "--key", help="the key to import", multiple=True, default=[])
@click.pass_context
def _import(ctx, path, latest_bkup, interactive, key):
    instance : MaaInstance = ctx.obj
    if latest_bkup and (pathes := instance.get_usr_bkups()):
        path = pathes[0]
    elif path:
        pass
    elif interactive:
        click.echo(f"available backups: {instance.get_usr_bkups()}")
        path = click.prompt("please select a backup", type=str)
    else:
        raise AssertionError("no backup found")
    
    instance._import(path, key)

@_cli.command("auto")
@click.option("-l", "--lifetime", help="the lifetime of the app", type=str)
@click.option("-c", "--capture-output", help="capture the output of the app", is_flag=True)
@click.pass_context
def _auto(ctx, lifetime, capture_output):
    instance : MaaInstance = ctx.obj
    res = instance._auto(lifetime, capture_output)
    if res:
        click.echo(res[0])
        click.echo(res[1])

@_cli.command("patch", help="patching the file, parts to patch, in the format of k/e/y=value")
@click.option("-p", "--path", help="the path to patch")
@click.option("-m", "--must-have-key", help="the key to patch must exist", is_flag=True)
@click.argument("parts", nargs=-1)
@click.pass_context
def _patch(ctx, path, must_have_key, parts):
    instance : MaaInstance = ctx.obj
    instance.patch(path, parts, must_have_key)

@_cli.command("op")
@click.pass_context
def _op(ctx):
    instance : MaaInstance = ctx.obj
    os.startfile(instance.path)

def cli():
    import sys

    # analyse the sys.argv
    # if no --name specified at the first part, then treat the first argument as the name
    name_specified = any(arg.startswith('--name') for arg in sys.argv)
    
    if not name_specified and not len(sys.argv) == 1:
        for i, arg in enumerate(sys.argv[1:], start=1):
            if not arg.startswith('-'):
                sys.argv[i] = f"--name={arg}"
                break
    try:
        _cli()
    except AssertionError as e:
        
        click.echo(f"error: {repr(e) or "not specified"}")

if __name__ == "__main__":
    cli()

    