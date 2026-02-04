import { useEffect, useRef } from "react";
import { connectSSE } from "@/services/api";
import { useAppDispatch } from "@/context/AppContext";
import type { StreamEvent } from "@/types/events";
import type { StatuteResult, CaseLawResult, FinalResult, FactPattern } from "@/types";

export function useSSE(runId: string | null) {
  const dispatch = useAppDispatch();
  const cleanupRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    if (!runId) return;

    const handleEvent = (event: StreamEvent) => {
      switch (event.type) {
        case "fact_pattern":
          dispatch({
            type: "SET_FACT_PATTERN",
            factPattern: event.payload as unknown as FactPattern,
          });
          break;

        case "wave1_started":
          dispatch({ type: "WAVE1_STARTED" });
          break;

        case "statute_found":
          dispatch({
            type: "STATUTE_FOUND",
            statute: event.payload as unknown as StatuteResult,
          });
          break;

        case "wave1_complete":
          dispatch({
            type: "WAVE1_COMPLETE",
            statutes: (event.payload as { statutes: StatuteResult[] }).statutes,
          });
          break;

        case "wave2_started":
          dispatch({ type: "WAVE2_STARTED" });
          break;

        case "caselaw_found":
          dispatch({
            type: "CASELAW_FOUND",
            caseLaw: event.payload as unknown as CaseLawResult,
          });
          break;

        case "wave2_complete":
          dispatch({
            type: "WAVE2_COMPLETE",
            caseLaw: (event.payload as { case_law: CaseLawResult[] }).case_law,
          });
          break;

        case "run_complete":
          dispatch({
            type: "RUN_COMPLETE",
            result: event.payload as unknown as FinalResult,
          });
          break;

        case "error":
          dispatch({
            type: "SET_ERROR",
            error: (event.payload as { message: string }).message,
          });
          break;
      }
    };

    const handleError = (error: Error) => {
      dispatch({ type: "SET_ERROR", error: error.message });
    };

    const handleClose = () => {
      // SSE connection closed
    };

    cleanupRef.current = connectSSE(runId, handleEvent, handleError, handleClose);

    return () => {
      cleanupRef.current?.();
    };
  }, [runId, dispatch]);
}
