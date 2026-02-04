import {
  createContext,
  useContext,
  useReducer,
  type ReactNode,
  type Dispatch,
} from "react";
import type {
  FactPattern,
  StatuteResult,
  CaseLawResult,
  FinalResult,
  ArchivedCase,
} from "@/types";

// === State ===

export type AppView = "input" | "results" | "archive";

export interface AppState {
  view: AppView;
  runId: string | null;
  inputText: string;
  factPattern: FactPattern | null;
  statutes: StatuteResult[];
  caseLaw: CaseLawResult[];
  isLoading: boolean;
  error: string | null;
  wave1Active: boolean;
  wave2Active: boolean;
  archivedCases: ArchivedCase[];
  selectedArchiveId: string | null;
}

const initialState: AppState = {
  view: "input",
  runId: null,
  inputText: "",
  factPattern: null,
  statutes: [],
  caseLaw: [],
  isLoading: false,
  error: null,
  wave1Active: false,
  wave2Active: false,
  archivedCases: [],
  selectedArchiveId: null,
};

// === Actions ===

export type AppAction =
  | { type: "SET_INPUT_TEXT"; text: string }
  | { type: "SUBMIT_CASE"; runId: string }
  | { type: "SET_FACT_PATTERN"; factPattern: FactPattern }
  | { type: "WAVE1_STARTED" }
  | { type: "STATUTE_FOUND"; statute: StatuteResult }
  | { type: "WAVE1_COMPLETE"; statutes: StatuteResult[] }
  | { type: "WAVE2_STARTED" }
  | { type: "CASELAW_FOUND"; caseLaw: CaseLawResult }
  | { type: "WAVE2_COMPLETE"; caseLaw: CaseLawResult[] }
  | { type: "RUN_COMPLETE"; result: FinalResult }
  | { type: "SET_ERROR"; error: string }
  | { type: "NEW_CASE" }
  | { type: "LOAD_ARCHIVE"; cases: ArchivedCase[] }
  | { type: "SELECT_ARCHIVE"; id: string }
  | { type: "VIEW_ARCHIVE_CASE"; archivedCase: ArchivedCase };

function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case "SET_INPUT_TEXT":
      return { ...state, inputText: action.text };

    case "SUBMIT_CASE":
      return {
        ...state,
        view: "results",
        runId: action.runId,
        isLoading: true,
        error: null,
        factPattern: null,
        statutes: [],
        caseLaw: [],
        wave1Active: false,
        wave2Active: false,
      };

    case "SET_FACT_PATTERN":
      return { ...state, factPattern: action.factPattern };

    case "WAVE1_STARTED":
      return { ...state, wave1Active: true };

    case "STATUTE_FOUND":
      return { ...state, statutes: [...state.statutes, action.statute] };

    case "WAVE1_COMPLETE":
      return {
        ...state,
        wave1Active: false,
        statutes: action.statutes,
      };

    case "WAVE2_STARTED":
      return { ...state, wave2Active: true };

    case "CASELAW_FOUND":
      return { ...state, caseLaw: [...state.caseLaw, action.caseLaw] };

    case "WAVE2_COMPLETE":
      return {
        ...state,
        wave2Active: false,
        caseLaw: action.caseLaw,
      };

    case "RUN_COMPLETE":
      return {
        ...state,
        isLoading: false,
        statutes: action.result.statutes,
        caseLaw: action.result.case_law,
      };

    case "SET_ERROR":
      return { ...state, isLoading: false, error: action.error };

    case "NEW_CASE":
      return {
        ...initialState,
        archivedCases: state.archivedCases,
      };

    case "LOAD_ARCHIVE":
      return { ...state, archivedCases: action.cases };

    case "SELECT_ARCHIVE":
      return { ...state, selectedArchiveId: action.id };

    case "VIEW_ARCHIVE_CASE": {
      const ac = action.archivedCase;
      return {
        ...state,
        view: "results",
        runId: ac.run_id,
        inputText: ac.input_text,
        factPattern: ac.result.fact_pattern,
        statutes: ac.result.statutes,
        caseLaw: ac.result.case_law,
        isLoading: false,
        error: null,
        wave1Active: false,
        wave2Active: false,
        selectedArchiveId: ac.id,
      };
    }

    default:
      return state;
  }
}

// === Context ===

const AppStateContext = createContext<AppState>(initialState);
const AppDispatchContext = createContext<Dispatch<AppAction>>(() => {});

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  return (
    <AppStateContext.Provider value={state}>
      <AppDispatchContext.Provider value={dispatch}>
        {children}
      </AppDispatchContext.Provider>
    </AppStateContext.Provider>
  );
}

export function useAppState() {
  return useContext(AppStateContext);
}

export function useAppDispatch() {
  return useContext(AppDispatchContext);
}
