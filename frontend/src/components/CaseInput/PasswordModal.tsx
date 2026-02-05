import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";

const API_BASE = import.meta.env.VITE_API_URL || "";

interface PasswordModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function PasswordModal({
  open,
  onOpenChange,
  onSuccess,
}: PasswordModalProps) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isValidating, setIsValidating] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsValidating(true);

    try {
      const response = await fetch(`${API_BASE}/api/validate-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ password }),
      });

      const data = await response.json();

      if (data.valid) {
        setPassword("");
        onOpenChange(false);
        onSuccess();
      } else {
        setError("Invalid password");
      }
    } catch {
      setError("Failed to validate password");
    } finally {
      setIsValidating(false);
    }
  };

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      setPassword("");
      setError("");
    }
    onOpenChange(newOpen);
  };

  return (
    <Sheet open={open} onOpenChange={handleOpenChange}>
      <SheetContent side="bottom" className="sm:max-w-md sm:mx-auto sm:rounded-t-lg">
        <SheetHeader>
          <SheetTitle>Enter Password</SheetTitle>
          <SheetDescription>
            Please enter the password to analyze the case.
          </SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="space-y-4 p-4 pt-0">
          <div className="space-y-2">
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              disabled={isValidating}
              autoFocus
            />
            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
          </div>
          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => handleOpenChange(false)}
              disabled={isValidating}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isValidating || !password}>
              {isValidating ? "Validating..." : "Submit"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}
