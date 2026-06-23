"""Core data structures for GapHarness.

The MVP stays on dataclasses instead of framework-specific models so experiments
remain easy to replay in a clean Python environment.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


OBLIGATIONS: Tuple[str, ...] = (
    "Observation",
    "Execution",
    "State",
    "Action",
    "Control",
    "Verification",
)

SUPPORTED_STATUSES: Tuple[str, ...] = ("supported", "unsupported", "clarify")


def frozen(values: Optional[Iterable[str]]) -> frozenset:
    return frozenset(values or [])


def ordered(values: Iterable[str]) -> Tuple[str, ...]:
    return tuple(sorted(set(values)))


@dataclass(frozen=True)
class ProfilerOutput:
    direct_llm_sufficient: bool
    obligations: frozenset
    required_capabilities: frozenset = field(default_factory=frozenset)
    output_contract: Mapping[str, Any] = field(default_factory=dict)
    forbidden_paths: Tuple[str, ...] = ()
    risk_level: str = "low"
    unsupported_possibility: Tuple[str, ...] = ()
    rationale: str = ""

    def to_json(self) -> Dict[str, Any]:
        return {
            "direct_llm_sufficient": self.direct_llm_sufficient,
            "obligations": ordered(self.obligations),
            "required_capabilities": ordered(self.required_capabilities),
            "output_contract": dict(self.output_contract),
            "forbidden_paths": list(self.forbidden_paths),
            "risk_level": self.risk_level,
            "unsupported_possibility": list(self.unsupported_possibility),
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class ModuleSpec:
    name: str
    provides: frozenset
    capabilities: frozenset
    cost: int
    requires_obligations: frozenset = field(default_factory=frozenset)
    requires_capabilities: frozenset = field(default_factory=frozenset)
    risk: Tuple[str, ...] = ()
    verifier: str = ""
    module_type: str = "runtime"

    def to_json(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "provides": ordered(self.provides),
            "capabilities": ordered(self.capabilities),
            "cost": self.cost,
            "requires_obligations": ordered(self.requires_obligations),
            "requires_capabilities": ordered(self.requires_capabilities),
            "risk": list(self.risk),
            "verifier": self.verifier,
            "module_type": self.module_type,
        }


@dataclass(frozen=True)
class CompiledHarness:
    status: str
    modules: Tuple[str, ...]
    obligations: frozenset
    capabilities: frozenset
    cost: int
    loop_template: str
    missing_obligations: Tuple[str, ...] = ()
    missing_capabilities: Tuple[str, ...] = ()
    reason: str = ""
    certificate: Mapping[str, Any] = field(default_factory=dict)

    def to_json(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "modules": list(self.modules),
            "obligations": ordered(self.obligations),
            "capabilities": ordered(self.capabilities),
            "cost": self.cost,
            "loop_template": self.loop_template,
            "missing_obligations": list(self.missing_obligations),
            "missing_capabilities": list(self.missing_capabilities),
            "reason": self.reason,
            "certificate": dict(self.certificate),
        }


@dataclass(frozen=True)
class TaskExample:
    task_id: str
    query: str
    gold_obligations: frozenset
    required_capabilities: frozenset
    oracle_minimal_harness: Tuple[str, ...]
    success_checker: str
    expected_failure_if_direct: str
    risk_level: str
    category: str
    expected_status: str = "supported"
    tags: Tuple[str, ...] = ()
    notes: str = ""
    gold_source: str = "synthetic_seed_needs_human_review"

    def to_json(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "query": self.query,
            "gold_obligations": ordered(self.gold_obligations),
            "required_capabilities": ordered(self.required_capabilities),
            "oracle_minimal_harness": list(self.oracle_minimal_harness),
            "success_checker": self.success_checker,
            "expected_failure_if_direct": self.expected_failure_if_direct,
            "risk_level": self.risk_level,
            "category": self.category,
            "expected_status": self.expected_status,
            "tags": list(self.tags),
            "notes": self.notes,
            "gold_source": self.gold_source,
        }

    @classmethod
    def from_json(cls, row: Mapping[str, Any]) -> "TaskExample":
        return cls(
            task_id=str(row["task_id"]),
            query=str(row["query"]),
            gold_obligations=frozen(row.get("gold_obligations")),
            required_capabilities=frozen(row.get("required_capabilities")),
            oracle_minimal_harness=tuple(row.get("oracle_minimal_harness", [])),
            success_checker=str(row.get("success_checker", "gold_coverage")),
            expected_failure_if_direct=str(row.get("expected_failure_if_direct", "")),
            risk_level=str(row.get("risk_level", "low")),
            category=str(row.get("category", "unknown")),
            expected_status=str(row.get("expected_status", "supported")),
            tags=tuple(row.get("tags", [])),
            notes=str(row.get("notes", "")),
            gold_source=str(row.get("gold_source", "unknown")),
        )


@dataclass(frozen=True)
class TraceEvent:
    step: int
    module: str
    event_type: str
    message: str
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def to_json(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RunResult:
    task_id: str
    system: str
    profiler: str
    harness: CompiledHarness
    trace: Tuple[TraceEvent, ...]
    final_output: str
    verifier_passed: bool
    verifier_failures: Tuple[str, ...]
    minimality_report: Mapping[str, Any]

    def to_json(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "system": self.system,
            "profiler": self.profiler,
            "harness": self.harness.to_json(),
            "trace": [event.to_json() for event in self.trace],
            "final_output": self.final_output,
            "verifier_passed": self.verifier_passed,
            "verifier_failures": list(self.verifier_failures),
            "minimality_report": dict(self.minimality_report),
        }
