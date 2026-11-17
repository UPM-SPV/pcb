#!/usr/bin/env python3

from __future__ import annotations
import click
from dominate import tags
import enum
import snakemd

import kicadcli

class OutputFormat(enum.Enum):
	MD = enum.auto()

	def format(self) -> str:
		# Only Markdown for now
		if self != OutputFormat.MD:
			raise ValueError("Only Markdown is supported")

		doc = snakemd.Document()

		doc.add_heading("3D Renders", 2)
		doc.add_table(
			[
				"Top", "Bottom"
			],
			[
				[
					str(snakemd.Paragraph([snakemd.Inline("Top", image="./board_top.png")])),
					str(snakemd.Paragraph([snakemd.Inline("Bottom", image="./board_bottom.png")]))
				]
			],
			align=[
				snakemd.Table.Align.CENTER,
				snakemd.Table.Align.CENTER
			]
		)

		return str(doc) + "\n" * 2


@click.command(help="Render 3D images and models.")
@click.option("--pro-file", required=True, help="Path to .kicad_pro file.",
    type=click.Path(
		exists=True, readable=True,
		file_okay=True, dir_okay=False,
	)
)
@click.option("--image", is_flag=True, help="Generate image renders of the front and back of the PCB.")
@click.option("--step", is_flag=True, help="Generate a 3D model.")
@click.option("--output", required=True, help="Path to output directory.",
    type=click.Path(
		writable=True,
		file_okay=False, dir_okay=True,
	)
)
@click.option("--output-format", default="md", help="Output report format.",
	type=click.Choice(OutputFormat, case_sensitive=False)
)
def render(
	pro_file: str,
	image: bool, step: bool,
	output: str,
	output_format: OutputFormat
):
	click.echo(f"Using '{click.style(pro_file, fg='blue')}'", err=True)

	if image:
		click.echo(f"Generating '{click.style("3D renders", fg='blue')}'", err=True)
		for side in ["top", "bottom"]:
			kicadcli.render_3d(
				pro_file, f"{output}/board_{side}.png",
				side,
				3840, 2160
			)
		report = output_format.format()
		with open(f"{output}/render-report.md", "w") as file:
			file.write(report)


	if step:
		click.echo(f"Generating '{click.style("STEP", fg='blue')}'", err=True)
		kicadcli.render_step(pro_file, f"{output}/board.step")
