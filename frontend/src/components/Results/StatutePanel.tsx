import { ScrollArea } from "@/components/ui/scroll-area";
import { StatuteCard } from "./StatuteCard";
import { StreamingIndicator } from "./StreamingIndicator";
import type { StatuteResult } from "@/types";
import { BookOpen } from "lucide-react";

interface StatutePanelProps {
  statutes: StatuteResult[];
  isSearching: boolean;
}

export function StatutePanel({ statutes, isSearching }: StatutePanelProps) {
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 p-4 border-b border-border">
        <BookOpen className="h-4 w-4 text-primary" />
        <h3 className="font-semibold">California Statutes</h3>
        {statutes.length > 0 && (
          <span className="text-xs text-muted-foreground">
            ({statutes.length})
          </span>
        )}
      </div>
      <ScrollArea className="flex-1 p-4">
        <StreamingIndicator
          label="Searching for relevant statutes..."
          active={isSearching}
        />
        {statutes.map((s, i) => (
          <StatuteCard key={`${s.code}-${s.section}-${i}`} statute={s} />
        ))}
        {!isSearching && statutes.length === 0 && (
          <p className="text-sm text-muted-foreground py-8 text-center">
            No statutes found yet.
          </p>
        )}
      </ScrollArea>
    </div>
  );
}
