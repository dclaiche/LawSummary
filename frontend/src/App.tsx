import { AppProvider, useAppState } from "@/context/AppContext";
import { AppShell } from "@/components/Layout/AppShell";
import { CaseInputScreen } from "@/components/CaseInput/CaseInputScreen";
import { ResultsScreen } from "@/components/Results/ResultsScreen";
import { useSSE } from "@/hooks/useSSE";

function AppContent() {
  const { view, runId } = useAppState();
  useSSE(runId);

  return (
    <AppShell>
      {view === "input" && <CaseInputScreen />}
      {view === "results" && <ResultsScreen />}
    </AppShell>
  );
}

function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}

export default App;
