#!/usr/bin/env python3

from __future__ import annotations
import click
from dominate import tags
from dominate.util import raw
import enum
import pandas
import shutil
import snakemd
import tempfile

import kicadcli


class OutputFormat(enum.Enum):
	MD = enum.auto()

	def format(
		self,
		grb: bool,
		bom: bool, bom_jlcpcb: bool,
		pos: bool, pos_jlcpcb: bool,
		schematic: bool
	) -> str:
		# Only Markdown for now
		if self != OutputFormat.MD:
			raise ValueError("Only Markdown is supported")

		doc = snakemd.Document()

		doc.add_heading("Fabrication outputs", 2)
		links = []
		if schematic:
			links.append(str(snakemd.Inline("Schematic", link="./schematic.pdf")))
		if bom:
			links.append(
				str(snakemd.Inline("BOM", link="./bom.csv")) +
				" " +
				"".join([ "(" + str(snakemd.Inline("JLCPCB", link="./bom_jlcpcb.csv")) + ")" ] if bom_jlcpcb else [])
			)
		if grb:
			links.append(str(snakemd.Inline("Gerbers", link="./grb.zip")))
		if pos:
			links.append(
				str(snakemd.Inline("POS", link="./pos.csv")) +
				" " +
				"".join([ "(" + str(snakemd.Inline("JLCPCB", link="./pos_jlcpcb.csv")) + ")" ] if pos_jlcpcb else [])
			)

		doc.add_unordered_list(links)

		return str(doc) + "\n" * 2

@click.command(help="Generate fabrication outputs.")
@click.option("--pro-file", required=True, help="Path to .kicad_pro file.",
    type=click.Path(
		exists=True, readable=True,
		file_okay=True, dir_okay=False,
	)
)
@click.option("--grb", is_flag=True, help="Generate gerbers.")
@click.option("--bom", is_flag=True, help="Generate BOM file.")
@click.option("--bom-jlcpcb", is_flag=True, help="Generate BOM file in JLCPCB format.")
@click.option("--pos", is_flag=True, help="Generate POS files.")
@click.option("--pos-jlcpcb", is_flag=True, help="Generate POS files in JLCPCB format.")
@click.option("--schematic", is_flag=True, help="Render schematic as a PDF.")
@click.option("--output", required=True, help="Path to output directory.",
    type=click.Path(
		writable=True,
		file_okay=False, dir_okay=True,
	)
)
@click.option("--output-format", default="md", help="Output report format.",
	type=click.Choice(OutputFormat, case_sensitive=False)
)
def fab(
	pro_file: str,
	grb: bool, bom: bool, bom_jlcpcb: bool, pos: bool, pos_jlcpcb: bool, schematic: bool,
	output: str, output_format: OutputFormat
):
	click.echo(f"Using '{click.style(pro_file, fg='blue')}'", err=True)

	if grb:
		click.echo(f"Generating '{click.style("gerbers", fg='blue')}'", err=True)
		tempdir = tempfile.mkdtemp()
		kicadcli.grb(pro_file, tempdir)
		shutil.make_archive(f"{output}/grb", "zip", tempdir)
		shutil.rmtree(tempdir)

	if bom or bom_jlcpcb:
		click.echo(f"Generating '{click.style("BOM", fg='blue')}'", err=True)
		kicadcli.bom(pro_file, f"{output}/bom.csv")

	if bom_jlcpcb:
		click.echo(f"Generating '{click.style("JLCPCB BOM", fg='blue')}'", err=True)
		bom_df = pandas.read_csv(f"{output}/bom.csv")
		bom_df = bom_df.rename(columns={
			"Reference": "Designator",
			"Value": "Comment",
			"LCSC Part No.": "JLCPCB Part Number"
		})
		bom_df = bom_df[["Comment", "Designator", "Footprint", "JLCPCB Part Number"]]
		bom_df.to_csv(f"{output}/bom_jlcpcb.csv", index=False)

	if pos or pos_jlcpcb:
		click.echo(f"Generating '{click.style("POS", fg='blue')}'", err=True)
		kicadcli.pos(pro_file, f"{output}/pos.csv")


	if pos_jlcpcb:
		click.echo(f"Generating '{click.style("JLCPCB POS", fg='blue')}'", err=True)
		pos_df = pandas.read_csv(f"{output}/pos.csv")
		pos_df['Rot'] = [rot if rot >= 0 else rot + 360 for rot in pos_df['Rot']]
		pos_df = pos_df.rename(columns={
			"Ref": "Designator",
			"PosX": "Mid X",
			"PosY": "Mid Y",
			"Side": "Layer",
			"Rot": "Rotation"
		})
		pos_df = pos_df[["Designator", "Mid X", "Mid Y", "Layer", "Rotation"]]
		pos_df.to_csv(f"{output}/pos_jlcpcb.csv", index=False)

	if schematic:
		click.echo(f"Generating '{click.style("schematic", fg='blue')}'", err=True)
		kicadcli.export_sch(pro_file, f"{output}/schematic.pdf")

	report = output_format.format(
		grb, bom, bom_jlcpcb, pos, pos_jlcpcb, schematic
	)
	with open(f"{output}/fab-report.md", "w") as file:
		file.write(report)
