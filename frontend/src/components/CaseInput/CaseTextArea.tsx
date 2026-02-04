import { Textarea } from "@/components/ui/textarea";

interface CaseTextAreaProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export function CaseTextArea({ value, onChange, disabled }: CaseTextAreaProps) {
  return (
    <Textarea
      placeholder="Enter the case narrative here... (minimum 20 characters)"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      className="min-h-[200px] resize-y text-base"
    />
  );
}
