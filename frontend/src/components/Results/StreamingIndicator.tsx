import { Loader2 } from "lucide-react";

interface StreamingIndicatorProps {
  label: string;
  active: boolean;
}

export function StreamingIndicator({ label, active }: StreamingIndicatorProps) {
  if (!active) return null;

  return (
    <div className="flex items-center gap-2 text-sm text-muted-foreground py-2">
      <Loader2 className="h-4 w-4 animate-spin" />
      <span>{label}</span>
    </div>
  );
}
