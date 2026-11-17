#!/usr/bin/env python3

import click
from rc import rc

@click.group()
def cli():
	pass

cli.add_command(rc)


if __name__ == '__main__':
	cli()
