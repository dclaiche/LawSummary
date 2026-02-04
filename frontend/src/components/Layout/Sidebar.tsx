import { ScrollArea } from "@/components/ui/scroll-area";
import { ArchiveList } from "@/components/Archive/ArchiveList";

export function Sidebar() {
  return (
    <aside className="w-64 border-r border-border bg-sidebar flex flex-col">
      <div className="p-4 border-b border-border">
        <h2 className="text-sm font-medium text-sidebar-foreground">
          Past Cases
        </h2>
      </div>
      <ScrollArea className="flex-1">
        <ArchiveList />
      </ScrollArea>
    </aside>
  );
}
