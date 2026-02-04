import { Scale } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAppState, useAppDispatch } from "@/context/AppContext";

export function TopBar() {
  const { view, isLoading } = useAppState();
  const dispatch = useAppDispatch();

  return (
    <header className="h-14 border-b border-border flex items-center justify-between px-6">
      <div className="flex items-center gap-2">
        <Scale className="h-5 w-5 text-primary" />
        <h1 className="text-lg font-semibold">Law Summary</h1>
      </div>

      {view === "results" && !isLoading && (
        <Button
          variant="outline"
          size="sm"
          onClick={() => dispatch({ type: "NEW_CASE" })}
        >
          New Case
        </Button>
      )}
    </header>
  );
}
