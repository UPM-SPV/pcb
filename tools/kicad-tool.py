#!/usr/bin/env python3

import click
from rc import rc
from fab import fab

@click.group()
def cli():
	pass

cli.add_command(rc)
cli.add_command(fab)


if __name__ == '__main__':
	cli()
