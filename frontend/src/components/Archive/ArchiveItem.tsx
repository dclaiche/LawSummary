import { Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ArchivedCase } from "@/types";

interface ArchiveItemProps {
  archivedCase: ArchivedCase;
  onView: () => void;
  onDelete: () => void;
}

export function ArchiveItem({ archivedCase, onView, onDelete }: ArchiveItemProps) {
  const preview = archivedCase.input_text.slice(0, 80);
  const date = new Date(archivedCase.created_at).toLocaleDateString();

  return (
    <div className="rounded-lg border border-border bg-card shadow-sm hover:shadow-md transition-shadow cursor-pointer">
      <div className="flex items-start gap-2 p-3">
        <button
          onClick={onView}
          className="flex-1 text-left min-w-0"
        >
          <p className="text-sm leading-snug line-clamp-3">{preview}...</p>
          <p className="text-xs text-muted-foreground mt-1.5">{date}</p>
        </button>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 shrink-0 text-muted-foreground hover:text-destructive"
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
        >
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}
