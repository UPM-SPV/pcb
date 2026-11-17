#!/usr/bin/env python3

from __future__ import annotations
import click
import cv2
from dominate import tags
from dominate.util import raw
import enum
import numpy as np
import os
import snakemd
from typing import Dict

import kicadcli
from ui import Octicon


def get_header_icon(status_set) -> Octicon:
	if "changed" in status_set or ("added" in status_set and "removed" in status_set):
		return Octicon.CHANGED
	elif "added" in status_set:
		return Octicon.ADDED
	elif "removed" in status_set:
		return Octicon.REMOVED
	else:
		return Octicon.UNCHANGED


class OutputFormat(enum.Enum):
	MD = enum.auto()

	def format(
		self,
		diffs: Dict[str, Dict[str, Dict[str, str]]]
	) -> str:
		# Only Markdown for now
		if self != OutputFormat.MD:
			raise ValueError("Only Markdown is supported")

		main_status_set = {
			section["status"]
			for group in diffs.values()
			for section in group.values()
		}
		main_icon = get_header_icon(main_status_set)

		doc = snakemd.Document()
		doc.add_raw(main_icon.render_title_md("Changes", 28, 2))

		for group_name, group in diffs.items():
			inner_doc = snakemd.Document()
			for section_name, section in group.items():
				section_icon = get_header_icon({section["status"]})
				inner_doc.add_raw(section_icon.render_title_md(section_name, 15, 4))
				inner_doc.add_block(
					snakemd.Paragraph([snakemd.Inline(section_name, image=f"<./{(section["path"])}>")])
				)

			group_status_set = { section["status"] for section in group.values() }
			group_icon = get_header_icon(group_status_set)
			group_details = tags.details(
				tags.summary(raw(group_icon.render_title(group_name, 20, "h3"))),
				raw("\n\n"),
				raw(str(inner_doc)),
				raw("\n\n")
			)
			doc.add_raw(str(group_details))

		return str(doc) + "\n" * 2


@click.command(help="Generate a visual diff of two KiCad project versions.")
@click.option("--before-pro-file", required=True, help="Path to original .kicad_pro file.",
    type=click.Path(
		exists=True, readable=True,
		file_okay=True, dir_okay=False,
	)
)
@click.option("--after-pro-file", required=True, help="Path to the new .kicad_pro file.",
    type=click.Path(
		exists=True, readable=True,
		file_okay=True, dir_okay=False,
	)
)
@click.option("--sch", is_flag=True, help="Run a diff on the schematic files.")
@click.option("--pcb", is_flag=True, help="Run a diff on the PCB.")
@click.option("--pcb-layers", help="Comma separated list of which layers to render.",
	default="F.Cu,In1.Cu,In2.Cu,B.Cu"
)
@click.option("--output", required=True, help="Path to output directory, contains 'diff-report.md', as well as all diff images.",
    type=click.Path(
		writable=True,
		file_okay=False, dir_okay=True,
	)
)
@click.option("--output-format", default="md", help="Output report format.",
	type=click.Choice(OutputFormat, case_sensitive=False)
)
def diff(
	before_pro_file: str, after_pro_file: str,
	sch: bool, pcb: bool,
	pcb_layers: str,
	output: str,
	output_format: OutputFormat
):
	click.echo(f"Using:", err=True)
	click.echo(f"	- New: '{click.style(after_pro_file, fg='blue')}'", err=True)
	click.echo(f"	- Old: '{click.style(before_pro_file, fg='blue')}'", err=True)

	os.makedirs(output, exist_ok=True)

	image_groups = {}

	if sch:
		click.echo(f"Rendering {click.style("before", fg='blue')} schematic", err=True)
		before_images = kicadcli.render_sch(before_pro_file)
		click.echo(f"Rendering {click.style("after", fg='blue')} schematic", err=True)
		after_images = kicadcli.render_sch(after_pro_file)
		image_groups["Schematic changes"] = {
			"before": before_images,
			"after": after_images
		}

	if pcb:
		click.echo(f"Rendering {click.style("before", fg='blue')} PCB", err=True)
		before_images = kicadcli.render_pcb(before_pro_file, pcb_layers)
		click.echo(f"Rendering {click.style("after", fg='blue')} PCB", err=True)
		after_images = kicadcli.render_pcb(after_pro_file, pcb_layers)
		image_groups["PCB changes"] = {
			"before": before_images,
			"after": after_images
		}

	diffs = {}
	for group_name, group in image_groups.items():
		before = group["before"]
		after = group["after"]
		all_keys = set(before.keys()) | set(after.keys())
		group_diff = {}

		for key in all_keys:
			if key not in before:
				image = after[key]
				group_diff[key] = {
					"path": f"{group_name}__{key}__new.png",
					"status": "new"
				}
			elif key not in after:
				image = before[key]
				group_diff[key] = {
					"path": f"{group_name}__{key}__removed.png",
					"status": "removed"
				}
			else:
				before_image = before[key]
				after_image = after[key]
				if np.array_equal(before_image, after_image):
					image = after[key]
					group_diff[key] = {
						"path": f"{group_name}__{key}__unchanged.png",
						"status": "unchanged",
					}
				else:
					click.echo(f"Diffing {click.style(key, fg='blue')} PCB", err=True)
					image, status = img_diff(before_image, after_image)
					group_diff[key] = {
						"path": f"{group_name}__{key}__changed.png",
						"status": status
					}

			cv2.imwrite(f"{output}/{group_diff[key]['path']}", image)

		diffs[group_name] = group_diff

	formatted_report = output_format.format(diffs)
	with open(f"{output}/diff-report.md", "w") as file:
		file.write(formatted_report)


def img_diff(before: np.ndarray, after: np.ndarray) -> Tuple[np.ndarray, str]:
	if before.shape != after.shape:
		after = cv2.resize(after, before.shape)

	_, before_inv = cv2.threshold(before, 200, 255, cv2.THRESH_BINARY_INV)
	_, after_inv = cv2.threshold(after, 200, 255, cv2.THRESH_BINARY_INV)

	same = cv2.bitwise_and(before_inv, after_inv)
	deleted = cv2.subtract(before_inv, after_inv)
	added = cv2.subtract(after_inv, before_inv)

	output_image = np.full((before_inv.shape[0], before_inv.shape[1], 3), 255, dtype=np.uint8)
	output_image[same > 0] = [88, 88, 88]
	output_image[deleted > 0] = [0, 0, 255]
	output_image[added > 0] = [0, 200, 0]

	changed_pixels = deleted.sum() + added.sum()
	deleted_pct = deleted.sum() / changed_pixels
	added_pct = added.sum() / changed_pixels

	if deleted_pct >= 0.8:
		status = "removed"
	elif added_pct >= 0.8:
		status = "new"
	else:
		status = "changed"

	return output_image, status
