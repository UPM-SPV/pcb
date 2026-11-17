#!/usr/bin/env python3

from __future__ import annotations
import enum
import json
from typing import Dict, List

class RcSeverity(enum.Enum):
	WARNING = enum.auto()
	ERROR = enum.auto()
	@staticmethod
	def from_string(string: str) -> RcSeverity:
		match string:
			case "error":
				return RcSeverity.ERROR
			case "warning":
				return RcSeverity.WARNING
			case _:
				return RcSeverity.ERROR


class ErcReport:
	# Sheet name to violation list
	_violations: Dict[str, List[RcViolation]]

	def __init__(self, violations: Dict[str, List[RcViolation]]) -> None:
		self._violations = violations

	@staticmethod
	def from_path(path: str) -> ErcReport:
		with open(path, 'r') as file:
			data = file.read()
		return ErcReport.from_json(data)

	@staticmethod
	def from_json(text: str) -> ErcReport:
		json_report = json.loads(text)
		sheet_reports = {
			sheet["path"]: parse_violation_list(sheet["violations"])
			for sheet in json_report["sheets"]
		}
		return ErcReport(sheet_reports)


	def violation_count(self, severity: RcSeverity | None = None) -> int:
		all_violations = self.all_erc_violations()
		return sum(1 for _ in filter(lambda v: v.severity == severity if severity else True, all_violations))

	def all_erc_violations(self) -> List[RcViolation]:
		return [violation for sheet in self.violations.values() for violation in sheet]
	@property
	def violations(self) -> Dict[str, List[RcViolation]]: return self._violations


class DrcReport:
	_violations: List[RcViolation]
	_unconnected_items: List[RcViolation]
	_schematic_parity: List[RcViolation]

	def __init__(
			self,
			violations: List[RcViolation],
			unconnected_items: List[RcViolation],
			schematic_parity: List[RcViolation]
		) -> None:
		self._violations = violations
		self._unconnected_items = unconnected_items
		self._schematic_parity = schematic_parity

	@staticmethod
	def from_path(path: str) -> DrcReport:
		with open(path, 'r') as file:
			data = file.read()
		return DrcReport.from_json(data)

	@staticmethod
	def from_json(text: str) -> DrcReport:
		json_report = json.loads(text)
		return DrcReport(
			violations=parse_violation_list(json_report["violations"]),
			unconnected_items=parse_violation_list(json_report["unconnected_items"]),
			schematic_parity=parse_violation_list(json_report["schematic_parity"]),
		)

	def violation_count(self, severity: RcSeverity | None = None) -> int:
		return sum(1 for _ in filter(lambda v: v.severity == severity if severity else True, self.all_drc_violations()))

	def all_drc_violations(self) -> List[RcViolation]:
		return [*self.violations, *self.unconnected_items, *self.schematic_parity]
	@property
	def violations(self) -> List[RcViolation]: return self._violations
	@property
	def unconnected_items(self) -> List[RcViolation]: return self._unconnected_items
	@property
	def schematic_parity(self) -> List[RcViolation]: return self._schematic_parity


def parse_violation_list(violations) -> List[RcViolation]:
	parsed = []
	for violation in violations:
		severity = RcSeverity.from_string(violation["severity"])
		description = violation["description"]
		violation_type = violation["type"]
		items = [item["description"] for item in violation["items"]]

		parsed.append(
			RcViolation(
				severity=severity,
				description=description,
				violation_type=violation_type,
				items=items
			)
		)
	return parsed


class RcViolation:
	_severity: RcSeverity
	_violation_type: str
	_description: str
	_items: List[str]

	def __init__(
			self,
			severity: RcSeverity,
			violation_type: str,
			description: str,
			items: List[str]
		) -> None:
		self._severity = severity
		self._violation_type = violation_type
		self._description = description
		self._items = items

	@property
	def severity(self) -> RcSeverity: return self._severity
	@property
	def violation_type(self) -> str: return self._violation_type
	@property
	def description(self) -> str: return self._description
	@property
	def items(self) -> List[str]: return self._items
