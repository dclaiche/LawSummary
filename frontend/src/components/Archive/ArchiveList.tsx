import { useArchive } from "@/hooks/useArchive";
import { ArchiveItem } from "./ArchiveItem";

export function ArchiveList() {
  const { archivedCases, viewCase, deleteCase } = useArchive();

  if (archivedCases.length === 0) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        No past cases yet.
      </div>
    );
  }

  return (
    <div className="p-2 space-y-2">
      {archivedCases.map((c) => (
        <ArchiveItem
          key={c.id}
          archivedCase={c}
          onView={() => viewCase(c.id)}
          onDelete={() => deleteCase(c.id)}
        />
      ))}
    </div>
  );
}
