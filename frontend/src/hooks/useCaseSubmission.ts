import { useCallback } from "react";
import { submitCase } from "@/services/api";
import { useAppDispatch } from "@/context/AppContext";

export function useCaseSubmission() {
  const dispatch = useAppDispatch();

  const submit = useCallback(
    async (text: string) => {
      try {
        const { run_id } = await submitCase(text);
        dispatch({ type: "SUBMIT_CASE", runId: run_id });
      } catch (err) {
        dispatch({
          type: "SET_ERROR",
          error: err instanceof Error ? err.message : "Failed to submit case",
        });
      }
    },
    [dispatch],
  );

  return { submit };
}
