export type EventType =
  | "run_started"
  | "fact_pattern"
  | "wave1_started"
  | "statute_progress"
  | "statute_found"
  | "wave1_complete"
  | "wave2_started"
  | "caselaw_progress"
  | "caselaw_found"
  | "wave2_complete"
  | "run_complete"
  | "error";

export interface StreamEvent {
  type: EventType;
  payload: Record<string, unknown>;
}
