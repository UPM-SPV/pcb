#!/usr/bin/env python3

from __future__ import annotations
import os
import pathlib
import subprocess
import tempfile

from kicadrc import DrcReport, ErcReport


def erc(kicad_pro_path: str) -> ErcReport:
	sch_filename = pathlib.Path(kicad_pro_path).with_suffix("").with_suffix(".kicad_sch")
	_, erc_filename = tempfile.mkstemp()
	subprocess.run(
		[
			"kicad-cli", "sch", "erc",
			"--format", "json",
			"--output", erc_filename,
			sch_filename
		],
		stdout = sys.stderr
	)
	erc_report = ErcReport.from_path(erc_filename)
	os.remove(erc_filename)
	return erc_report


def drc(kicad_pro_path: str) -> DrcReport:
	pcb_filename = pathlib.Path(kicad_pro_path).with_suffix("").with_suffix(".kicad_pcb")
	_, drc_filename = tempfile.mkstemp()
	subprocess.run(
		[
			"kicad-cli", "pcb", "drc",
			"--format", "json",
			"--output", drc_filename,
			pcb_filename
		],
		stdout = sys.stderr
	)
	drc_report = DrcReport.from_path(drc_filename)
	os.remove(drc_filename)
	return drc_report


def grb(kicad_pro_path: str, output_path: str) -> None:
	pcb_filename = pathlib.Path(kicad_pro_path).with_suffix("").with_suffix(".kicad_pcb")
	subprocess.run(
		[
			"kicad-cli", "pcb", "export", "gerbers",
			"--output", output_path,
			pcb_filename
		],
		stdout = sys.stderr
	)
	subprocess.run(
		[
			"kicad-cli", "pcb", "export", "drill",
			"--output", output_path,
			pcb_filename
		],
		stdout = sys.stderr
	)


def pos(kicad_pro_path: str, output_path: str) -> None:
	pcb_filename = pathlib.Path(kicad_pro_path).with_suffix("").with_suffix(".kicad_pcb")
	subprocess.run(
		[
			"kicad-cli", "pcb", "export", "pos",
			"--format", "csv",
			"--units", "mm",
			"--exclude-dnp",
			"--output", output_path,
			pcb_filename
		],
		stdout = sys.stderr
	)


def bom(kicad_pro_path: str, output_path: str) -> None:
	sch_filename = pathlib.Path(kicad_pro_path).with_suffix("").with_suffix(".kicad_sch")
	subprocess.run(
		[
			"kicad-cli", "sch", "export", "bom",
			"--output", output_path,
			"--fields", "*",
			"--group-by", "Value,Footprint",
			"--exclude-dnp",
			sch_filename
		],
		stdout = sys.stderr
	)


def export_sch(kicad_pro_path: str, output_path: str) -> None:
	sch_filename = pathlib.Path(kicad_pro_path).with_suffix("").with_suffix(".kicad_sch")
	subprocess.run(
		[
			"kicad-cli", "sch", "export", "pdf",
			"--output", output_path,
			sch_filename
		],
		stdout = sys.stderr
	)


def render_step(kicad_pro_path: str, output_path: str) -> None:
	pcb_filename = pathlib.Path(kicad_pro_path).with_suffix("").with_suffix(".kicad_pcb")
	subprocess.run(
		[
			"kicad-cli", "pcb", "export", "step",
			"--no-dnp",
			"--output", output_path,
			pcb_filename
		],
		stdout = sys.stderr
	)


def render_3d(kicad_pro_path: str, output_path: str, side: str, width: int, height: int) -> None:
	pcb_filename = pathlib.Path(kicad_pro_path).with_suffix("").with_suffix(".kicad_pcb")
	subprocess.run(
		[
			"xvfb-run", "-a", "kicad-cli", "pcb", "render",
			"--side", side,
			"--width", str(width),
			"--height", str(height),
			"--quality", "user",
			"--background", "transparent",
			"--preset", "3d_render",
			"--output", output_path,
			pcb_filename
		],
		stdout = sys.stderr
	)
	subprocess.run(
		[
			"magick",
			output_path,
			"-trim", "+repage",
			"-bordercolor", "transparent",
			"-border", "20",
			output_path,
		],
		stdout = sys.stderr
	)
