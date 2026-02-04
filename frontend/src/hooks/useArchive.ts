import { useCallback, useEffect } from "react";
import { useAppState, useAppDispatch } from "@/context/AppContext";
import type { ArchivedCase, FinalResult } from "@/types";

const STORAGE_KEY = "law-summary-archive";

function loadFromStorage(): ArchivedCase[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

function saveToStorage(cases: ArchivedCase[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(cases));
}

export function useArchive() {
  const { archivedCases } = useAppState();
  const dispatch = useAppDispatch();

  // Load on mount
  useEffect(() => {
    const cases = loadFromStorage();
    dispatch({ type: "LOAD_ARCHIVE", cases });
  }, [dispatch]);

  const saveCase = useCallback(
    (inputText: string, runId: string, result: FinalResult) => {
      const newCase: ArchivedCase = {
        id: crypto.randomUUID(),
        run_id: runId,
        input_text: inputText,
        result,
        created_at: new Date().toISOString(),
      };
      const updated = [newCase, ...archivedCases];
      saveToStorage(updated);
      dispatch({ type: "LOAD_ARCHIVE", cases: updated });
    },
    [archivedCases, dispatch],
  );

  const deleteCase = useCallback(
    (id: string) => {
      const updated = archivedCases.filter((c) => c.id !== id);
      saveToStorage(updated);
      dispatch({ type: "LOAD_ARCHIVE", cases: updated });
    },
    [archivedCases, dispatch],
  );

  const viewCase = useCallback(
    (id: string) => {
      const found = archivedCases.find((c) => c.id === id);
      if (found) {
        dispatch({ type: "VIEW_ARCHIVE_CASE", archivedCase: found });
      }
    },
    [archivedCases, dispatch],
  );

  return { archivedCases, saveCase, deleteCase, viewCase };
}
