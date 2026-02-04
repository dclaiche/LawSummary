import { Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ArchivedCase } from "@/types";

interface ArchiveItemProps {
  archivedCase: ArchivedCase;
  onView: () => void;
  onDelete: () => void;
}

export function ArchiveItem({ archivedCase, onView, onDelete }: ArchiveItemProps) {
  const preview = archivedCase.input_text.slice(0, 60);
  const date = new Date(archivedCase.created_at).toLocaleDateString();

  return (
    <div className="group flex items-center gap-1 p-2 rounded-md hover:bg-sidebar-accent cursor-pointer">
      <button
        onClick={onView}
        className="flex-1 text-left min-w-0"
      >
        <p className="text-sm truncate">{preview}...</p>
        <p className="text-xs text-muted-foreground">{date}</p>
      </button>
      <Button
        variant="ghost"
        size="icon"
        className="h-6 w-6 opacity-0 group-hover:opacity-100 shrink-0"
        onClick={(e) => {
          e.stopPropagation();
          onDelete();
        }}
      >
        <Trash2 className="h-3 w-3" />
      </Button>
    </div>
  );
}
