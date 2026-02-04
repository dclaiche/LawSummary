import { useEffect, useRef } from "react";
import { useAppState } from "@/context/AppContext";
import { useArchive } from "@/hooks/useArchive";
import { StatutePanel } from "./StatutePanel";
import { CaseLawPanel } from "./CaseLawPanel";
import { Separator } from "@/components/ui/separator";
import { Loader2 } from "lucide-react";

export function ResultsScreen() {
  const {
    runId,
    inputText,
    factPattern,
    statutes,
    caseLaw,
    isLoading,
    error,
    wave1Active,
    wave2Active,
    selectedArchiveId,
  } = useAppState();
  const { saveCase } = useArchive();
  const savedRef = useRef(false);

  // Auto-save when run completes (skip if viewing an archived case)
  useEffect(() => {
    if (
      !isLoading &&
      !error &&
      runId &&
      factPattern &&
      (statutes.length > 0 || caseLaw.length > 0) &&
      !savedRef.current &&
      !selectedArchiveId
    ) {
      savedRef.current = true;
      saveCase(inputText, runId, {
        run_id: runId,
        fact_pattern: factPattern,
        statutes,
        case_law: caseLaw,
      });
    }
  }, [isLoading, error, runId, factPattern, statutes, caseLaw, inputText, saveCase, selectedArchiveId]);

  // Reset saved ref when runId changes
  useEffect(() => {
    savedRef.current = false;
  }, [runId]);

  return (
    <div className="flex flex-col h-full">
      {/* Fact Pattern Summary */}
      {factPattern && (
        <div className="p-4 border-b border-border bg-muted/30">
          <h3 className="font-semibold mb-1">Fact Pattern</h3>
          <p className="text-sm text-muted-foreground">{factPattern.summary}</p>
          {factPattern.issues.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {factPattern.issues.map((issue) => (
                <span
                  key={issue.id}
                  className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full"
                >
                  {issue.label}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Loading state before fact pattern */}
      {isLoading && !factPattern && (
        <div className="flex items-center justify-center p-8 gap-2">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span className="text-muted-foreground">Analyzing case narrative...</span>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="p-4 m-4 text-sm text-destructive bg-destructive/10 rounded-md">
          {error}
        </div>
      )}

      {/* Split Panel */}
      <div className="flex-1 flex min-h-0">
        <div className="flex-1 min-h-0 min-w-0">
          <StatutePanel statutes={statutes} isSearching={wave1Active} />
        </div>
        <Separator orientation="vertical" />
        <div className="flex-1 min-h-0 min-w-0">
          <CaseLawPanel caseLaw={caseLaw} isSearching={wave2Active} />
        </div>
      </div>
    </div>
  );
}
