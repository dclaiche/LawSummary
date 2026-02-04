export interface LegalIssue {
  id: string;
  label: string;
  description: string;
  relevant_facts: string[];
}

export interface FactPattern {
  summary: string;
  parties: string[];
  issues: LegalIssue[];
  jurisdiction: string;
}

export interface StatuteResult {
  code: string;
  section: string;
  title: string;
  full_text: string;
  url: string;
  relevance_summary: string;
  case_snippet: string;
  confidence: number;
  source_issue_id: string;
}

export interface CaseLawResult {
  case_name: string;
  citation: string;
  court: string;
  date_filed: string;
  url: string;
  snippet: string;
  relevance_summary: string;
  related_statutes: string[];
  confidence: number;
  source_issue_id: string;
}

export interface FinalResult {
  run_id: string;
  fact_pattern: FactPattern;
  statutes: StatuteResult[];
  case_law: CaseLawResult[];
}

export interface CaseResponse {
  run_id: string;
}

export interface ArchivedCase {
  id: string;
  run_id: string;
  input_text: string;
  result: FinalResult;
  created_at: string;
}
