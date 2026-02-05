import { useState } from "react";
import { Button } from "@/components/ui/button";
import { CaseTextArea } from "./CaseTextArea";
import { PasswordModal } from "./PasswordModal";
import { useCaseSubmission } from "@/hooks/useCaseSubmission";
import { useAppState, useAppDispatch } from "@/context/AppContext";
import { Send } from "lucide-react";

export function CaseInputScreen() {
  const { inputText, isLoading, error } = useAppState();
  const dispatch = useAppDispatch();
  const { submit } = useCaseSubmission();
  const [localText, setLocalText] = useState(inputText);
  const [showPasswordModal, setShowPasswordModal] = useState(false);

  const canSubmit = localText.length >= 20 && !isLoading;

  const handleSubmit = () => {
    if (!canSubmit) return;
    dispatch({ type: "SET_INPUT_TEXT", text: localText });
    submit(localText);
  };

  const handleAnalyzeClick = () => {
    if (!canSubmit) return;
    setShowPasswordModal(true);
  };

  return (
    <div className="flex items-center justify-center h-full p-8">
      <div className="w-full max-w-2xl space-y-4">
        <div className="text-center space-y-2 mb-8">
          <h2 className="text-2xl font-bold">Analyze a Case</h2>
          <p className="text-muted-foreground">
            Enter a case narrative and we'll find relevant California statutes
            and case law.
          </p>
        </div>

        <CaseTextArea
          value={localText}
          onChange={setLocalText}
          disabled={isLoading}
        />

        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            {localText.length} / 20,000 characters
          </span>
          <Button onClick={handleAnalyzeClick} disabled={!canSubmit}>
            <Send className="mr-2 h-4 w-4" />
            Analyze
          </Button>
        </div>

        {error && (
          <div className="text-sm text-destructive bg-destructive/10 p-3 rounded-md">
            {error}
          </div>
        )}
      </div>

      <PasswordModal
        open={showPasswordModal}
        onOpenChange={setShowPasswordModal}
        onSuccess={handleSubmit}
      />
    </div>
  );
}
