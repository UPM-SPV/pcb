#!/usr/bin/env python3

import click
from rc import rc
from fab import fab
from render import render

@click.group()
def cli():
	pass

cli.add_command(rc)
cli.add_command(fab)
cli.add_command(render)


if __name__ == '__main__':
	cli()
