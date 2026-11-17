#!/usr/bin/env python3

from __future__ import annotations
import enum
import snakemd

class Octicon(enum.Enum):
	SUCCESS = enum.auto()
	WARN = enum.auto()
	ERROR = enum.auto()

	ADDED = enum.auto()
	REMOVED = enum.auto()
	CHANGED = enum.auto()
	UNCHANGED = enum.auto()

	def render_title(self, title: str, icon_size: int, heading_size: str) -> str:
		return f"<{heading_size}>{self.html(icon_size)}&nbsp;{title}<{heading_size}/>"

	def render_title_md(self, title: str, icon_size: int, heading_size: int) -> str:
		doc = snakemd.Document()
		doc.add_heading(f"{self.html(icon_size)}&nbsp;{title}", heading_size)
		return str(doc)

	def html(self, size: int) -> str:
		ICON_DATA = {
			Octicon.SUCCESS: {
				"name": "issue-closed",
				"color": "0fbf3e",
				"alt": "Success",
			},
			Octicon.WARN: {
				"name": "alert",
				"color": "c7a60b",
				"alt": "Warning",
			},
			Octicon.ERROR: {
				"name": "x-circle",
				"color": "fa4549",
				"alt": "Error",
			},

			Octicon.ADDED: {
				"name": "diff-added",
				"color": "0fbf3e",
				"alt": "Added",
			},
			Octicon.REMOVED: {
				"name": "diff-removed",
				"color": "fa4549",
				"alt": "Removed",
			},
			Octicon.CHANGED: {
				"name": "diff-modified",
				"color": "c7a60b",
				"alt": "Changed",
			},
			Octicon.UNCHANGED: {
				"name": "diff-ignored",
				"color": "1a61fe",
				"alt": "Unchanged",
			},
		}
		icon = ICON_DATA[self]

		return f'<a href="#"><img src="https://colored-octicons.vercel.app/{icon['name']}/{icon['color']}" width="{size}" height="{size}" align="absmiddle" aria-hidden alt="{icon['alt']}" /></a>'
