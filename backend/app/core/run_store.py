import uuid
from dataclasses import dataclass, field

from app.models.schemas import FactPattern, StatuteResult, CaseLawResult, FinalResult


@dataclass
class RunState:
    run_id: str
    input_text: str
    status: str = "pending"  # pending | running | complete | error
    fact_pattern: FactPattern | None = None
    statutes: list[StatuteResult] = field(default_factory=list)
    case_law: list[CaseLawResult] = field(default_factory=list)
    error: str | None = None

    def to_final_result(self) -> FinalResult:
        return FinalResult(
            run_id=self.run_id,
            fact_pattern=self.fact_pattern or FactPattern(summary="", parties=[], issues=[]),
            statutes=self.statutes,
            case_law=self.case_law,
        )


class RunStore:
    def __init__(self) -> None:
        self._runs: dict[str, RunState] = {}

    def create_run(self, input_text: str) -> RunState:
        run_id = uuid.uuid4().hex[:12]
        run = RunState(run_id=run_id, input_text=input_text)
        self._runs[run_id] = run
        return run

    def get_run(self, run_id: str) -> RunState | None:
        return self._runs.get(run_id)

    def list_runs(self) -> list[RunState]:
        return list(self._runs.values())


run_store = RunStore()
