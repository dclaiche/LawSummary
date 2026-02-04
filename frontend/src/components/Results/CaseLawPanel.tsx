import { ScrollArea } from "@/components/ui/scroll-area";
import { CaseLawCard } from "./CaseLawCard";
import { StreamingIndicator } from "./StreamingIndicator";
import type { CaseLawResult } from "@/types";
import { Gavel } from "lucide-react";

interface CaseLawPanelProps {
  caseLaw: CaseLawResult[];
  isSearching: boolean;
}

export function CaseLawPanel({ caseLaw, isSearching }: CaseLawPanelProps) {
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 p-4 border-b border-border">
        <Gavel className="h-4 w-4 text-primary" />
        <h3 className="font-semibold">Case Law</h3>
        {caseLaw.length > 0 && (
          <span className="text-xs text-muted-foreground">
            ({caseLaw.length})
          </span>
        )}
      </div>
      <ScrollArea className="flex-1 p-4">
        <StreamingIndicator
          label="Searching for relevant case law..."
          active={isSearching}
        />
        {caseLaw.map((c, i) => (
          <CaseLawCard key={`${c.case_name}-${i}`} caseLaw={c} />
        ))}
        {!isSearching && caseLaw.length === 0 && (
          <p className="text-sm text-muted-foreground py-8 text-center">
            No case law found yet.
          </p>
        )}
      </ScrollArea>
    </div>
  );
}
