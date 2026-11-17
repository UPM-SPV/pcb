#!/usr/bin/env python3

from __future__ import annotations
import click
from dominate import tags
from dominate.util import raw
import enum
import snakemd
import textwrap
from typing import Dict, List

import kicadcli
from kicadrc import DrcReport, ErcReport, RcSeverity, RcViolation
from ui import Octicon

class RcSummary:
	_erc_warnings: int
	_erc_errors: int
	_drc_warnings: int
	_drc_errors: int

	def __init__(self) -> None:
		self._erc_warnings = 0
		self._erc_errors = 0
		self._drc_warnings = 0
		self._drc_errors = 0

	def success(self) -> bool:
		return self.report_count() == 0

	def aggregate(self) -> str:
		if self._erc_errors > 0 or self._drc_errors > 0:
			return "error"
		if self._erc_warnings > 0 or self._drc_warnings > 0:
			return "warning"
		return "ok"

	def report_count(self) -> int:
		return self.erc_warnings + self.erc_errors + self.drc_warnings + self.drc_errors

	def __str__(self) -> str:
		return textwrap.dedent(f"""\
			RC_AGGREGATE={self.aggregate()}
			RC_TOTAL_VIOLATIONS={self.report_count()}
			RC_ERC_WARNINGS={self.erc_warnings}
			RC_ERC_ERRORS={self.erc_errors}
			RC_DRC_WARNINGS={self.drc_warnings}
			RC_DRC_ERRORS={self.drc_errors}
		""")

	@property
	def erc_warnings(self) -> int: return self._erc_warnings
	@property
	def erc_errors(self) -> int: return self._erc_errors
	@property
	def drc_warnings(self) -> int: return self._drc_warnings
	@property
	def drc_errors(self) -> int: return self._drc_errors
	@erc_warnings.setter
	def erc_warnings(self, value: int) -> None: self._erc_warnings = value
	@erc_errors.setter
	def erc_errors(self, value: int) -> None: self._erc_errors = value
	@drc_warnings.setter
	def drc_warnings(self, value: int) -> None: self._drc_warnings = value
	@drc_errors.setter
	def drc_errors(self, value: int) -> None: self._drc_errors = value


def split_line_breaks(text: str) -> List[str | tags.dom_tag]:
	lines = text.split("\n")
	return [
		element
		for i, line in enumerate(lines)
		for element in ([line, tags.br()] if i < len(lines) - 1 else [line])
	]



def render_violation_table(violations: List[RcViolation]) -> str:
	table = tags.table(align="center")
	table.add_raw_string(textwrap.dedent(f"""\
			<thead>
				<tr>
					<th align="center"><b>Severity</b></th>
					<th align="center"><b>Description</b></th>
					<th align="center"><b>Items</b></th>
				</tr>
			</thead>
		""")
	)

	tbody = tags.tbody()
	with tbody:
		for violation in violations:
			item_count = max(len(violation.items), 1)
			match violation.severity:
				case RcSeverity.ERROR:
					severity = Octicon.ERROR.html(25)
				case RcSeverity.WARNING:
					severity = Octicon.WARN.html(25)
			with tags.tr():
				tags.td(raw(severity), rowspan=item_count, align="center")
				tags.td(split_line_breaks(violation.description), align="center", rowspan=item_count)
				if len(violation.items) != 0:
					tags.td(split_line_breaks(violation.items[0]), align="center")

			for item in violation.items[1:]:
				with tags.tr():
					tags.td(split_line_breaks(item), align="center")

	table.add(tbody)
	return str(table)


def render_section_title(title: str, severity: Octicon) -> str:
	if severity == Octicon.SUCCESS:
		doc = snakemd.Document()
		doc.add_heading(f"{Octicon.SUCCESS.html(28)} {title}", level=2)
		doc.add_heading("$\\color{#0fbf3e}{\\textsf{All checks passed}}$", level=3)
		return str(doc)

	return f"<h2>{severity.html(28)}&nbsp;{title}</h2>"


def render_violations_section(title: str, violation_dict: Dict[str, List[RcViolation]]) -> str:
	doc = snakemd.Document()

	total_violations = sum(len(violations) for violations in violation_dict.values())

	if total_violations == 0:
		doc.add_raw(render_section_title(title, Octicon.SUCCESS))
		return str(doc)

	all_violations = [violation for violation_list in violation_dict.values() for violation in violation_list]
	is_error = next((violation for violation in all_violations if violation.severity == RcSeverity.ERROR), None) is not None

	for subsection, violations in violation_dict.items():
		if len(violations) == 0:
			continue
		doc.add_heading(subsection, 3)
		table = render_violation_table(violations)
		doc.add_raw(str(table))

	title_icon = Octicon.ERROR if is_error else Octicon.WARN
	title = render_section_title(title, title_icon)
	section = tags.details(
		tags.summary(raw(title)),
		raw("\n\n"),
		raw(str(doc)),
		raw("\n\n")
	)
	return str(section)


class OutputFormat(enum.Enum):
	MD = enum.auto()

	def format(
		self,
		summary: RcSummary,
		erc_report: ErcReport | None,
		drc_report: DrcReport | None
	) -> str:
		# Only Markdown for now
		if self != OutputFormat.MD:
			raise ValueError("Only Markdown is supported")

		doc = snakemd.Document()

		if erc_report:
			violations = {
				f"Sheet: `{sheet_name}`": violations
				for sheet_name, violations in erc_report.violations.items()
			}
			doc.add_raw(render_violations_section(
				"Electrical Rules Check",
				violations
			))

		if drc_report:
			violations = {
				"Violations": drc_report.violations,
				"Unconnected items": drc_report.unconnected_items,
				"Schematic parity": drc_report.schematic_parity
			}
			doc.add_raw(render_violations_section(
				"Design Rules Check",
				violations
			))

		return str(doc) + "\n" * 2


@click.command(help="Perform rules checking on a KiCad project and generate a report.")
@click.option("--pro-file", required=True, help="Path to .kicad_pro file.",
    type=click.Path(
		exists=True, readable=True,
		file_okay=True, dir_okay=False,
	)
)
@click.option("--erc", is_flag=True, help="Run ERC on the schematic files.")
@click.option("--drc", is_flag=True, help="Run DRC on the PCB.")
@click.option("--output", help="Path to output file, prints to stdout if not specified.",
    type=click.Path(
		writable=True,
		file_okay=True, dir_okay=False,
	)
)
@click.option("--output-format", default="md", help="Output report format.",
	type=click.Choice(OutputFormat, case_sensitive=False)
)
@click.option("--summary",
    "summary_path",
    help="""Path to shell-friendly summary output file, leave empty to disable.

	\b
	Contains:
		RC_AGGREGATE=error|warning|ok	# Maximum severity found
		RC_TOTAL_VIOLATIONS=num			# Aggregate number of raised violations
		RC_ERC_WARNINGS=num				# Number of generated ERC warnings
		RC_ERC_ERRORS=num				# Number of generated ERC errors
		RC_DRC_WARNINGS=num				# Number of generated DRC warnings
		RC_DRC_ERRORS=num				# Number of generated DRC errors
	""",
	type=click.Path(
		writable=True,
		file_okay=True, dir_okay=False,
	)
)
def rc(
	pro_file: str,
	erc: bool, drc: bool,
	output: str | None, output_format: OutputFormat,
	summary_path: str | None
):
	click.echo(f"Using '{click.style(pro_file, fg='blue')}'", err=True)
	summary = RcSummary()

	if erc:
		erc_report = kicadcli.erc(pro_file)
		summary.erc_warnings = erc_report.violation_count(RcSeverity.WARNING)
		summary.erc_errors = erc_report.violation_count(RcSeverity.ERROR)


	if drc:
		drc_report = kicadcli.drc(pro_file)
		summary.drc_warnings = drc_report.violation_count(RcSeverity.WARNING)
		summary.drc_errors = drc_report.violation_count(RcSeverity.ERROR)


	if summary_path:
		with open(summary_path, 'w') as file:
			file.write(str(summary))
		click.echo(f"Wrote summary to '{click.style(summary_path, fg='blue')}'", err=True)


	formatted_report = output_format.format(summary, erc_report, drc_report)
	if output:
		with open(output, 'w') as file:
			file.write(formatted_report)
		click.echo(f"Wrote report to '{click.style(output, fg='blue')}'", err=True)
	else:
		click.echo(formatted_report)
