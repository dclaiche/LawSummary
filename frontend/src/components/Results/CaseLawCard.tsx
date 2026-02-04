import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { CaseLawResult } from "@/types";
import { ExternalLink } from "lucide-react";

interface CaseLawCardProps {
  caseLaw: CaseLawResult;
}

export function CaseLawCard({ caseLaw }: CaseLawCardProps) {
  const confidenceColor =
    caseLaw.confidence >= 0.7
      ? "bg-green-100 text-green-800"
      : caseLaw.confidence >= 0.5
        ? "bg-yellow-100 text-yellow-800"
        : "bg-red-100 text-red-800";

  return (
    <Card className="mb-3">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div>
            <CardTitle className="text-base">{caseLaw.case_name}</CardTitle>
            <CardDescription>
              {caseLaw.citation} — {caseLaw.court}
              {caseLaw.date_filed ? ` (${caseLaw.date_filed})` : ""}
            </CardDescription>
          </div>
          <Badge className={confidenceColor} variant="secondary">
            {Math.round(caseLaw.confidence * 100)}%
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm">{caseLaw.relevance_summary}</p>

        {caseLaw.snippet && (
          <blockquote className="text-sm border-l-2 border-primary/30 pl-3 italic text-muted-foreground">
            "{caseLaw.snippet}"
          </blockquote>
        )}

        {caseLaw.related_statutes.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {caseLaw.related_statutes.map((s) => (
              <Badge key={s} variant="outline" className="text-xs">
                {s}
              </Badge>
            ))}
          </div>
        )}

        {caseLaw.url && (
          <a
            href={caseLaw.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
          >
            <ExternalLink className="h-3 w-3" />
            View on CourtListener
          </a>
        )}
      </CardContent>
    </Card>
  );
}
