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

