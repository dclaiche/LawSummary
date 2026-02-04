import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { StatuteResult } from "@/types";
import { ExternalLink } from "lucide-react";

interface StatuteCardProps {
  statute: StatuteResult;
}

export function StatuteCard({ statute }: StatuteCardProps) {
  const confidenceColor =
    statute.confidence >= 0.7
      ? "bg-green-100 text-green-800"
      : statute.confidence >= 0.5
        ? "bg-yellow-100 text-yellow-800"
        : "bg-red-100 text-red-800";

  return (
    <Card className="mb-3">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div>
            <CardTitle className="text-base">
              {statute.code} Section {statute.section}
            </CardTitle>
            <CardDescription>{statute.title}</CardDescription>
          </div>
          <Badge className={confidenceColor} variant="secondary">
            {Math.round(statute.confidence * 100)}%
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm">{statute.relevance_summary}</p>

        {statute.case_snippet && (
          <div className="text-sm bg-muted p-2 rounded-md">
            <span className="font-medium">Matching facts: </span>
            {statute.case_snippet}
          </div>
        )}

        {statute.full_text && (
          <details className="text-sm">
            <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
              View statute text
            </summary>
            <pre className="mt-2 whitespace-pre-wrap text-xs bg-muted p-3 rounded-md max-h-48 overflow-y-auto">
              {statute.full_text}
            </pre>
          </details>
        )}

        {statute.url && (
          <a
            href={statute.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
          >
            <ExternalLink className="h-3 w-3" />
            View on LegInfo
          </a>
        )}
      </CardContent>
    </Card>
  );
}
