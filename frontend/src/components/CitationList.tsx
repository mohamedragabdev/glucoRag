import React, { useState } from 'react';
import { BookOpen, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import type { Translations } from '../i18n/translations';

export interface Citation {
  id?: number;
  message_id?: number;
  document_id: string;
  chunk_id: string;
  source_title: string;
  page_number?: number | null;
}

interface CitationListProps {
  citations: Citation[];
  t: Translations;
}

export const CitationList: React.FC<CitationListProps> = ({ citations, t }) => {
  const [expanded, setExpanded] = useState(false);

  if (!citations || citations.length === 0) {
    return null;
  }

  return (
    <div className="mt-3 pt-3 border-t border-slate-200/80 dark:border-slate-800 text-xs">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 font-medium text-emerald-700 dark:text-emerald-400 hover:text-emerald-800 dark:hover:text-emerald-300 transition-colors cursor-pointer"
      >
        <BookOpen className="w-3.5 h-3.5" />
        <span>{t.evidenceSources} ({citations.length})</span>
        {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
      </button>

      {expanded && (
        <div className="mt-2.5 space-y-1.5">
          {citations.map((cit, idx) => (
            <div
              key={cit.id || cit.chunk_id || idx}
              className="flex items-center justify-between bg-emerald-50/80 dark:bg-emerald-950/30 border border-emerald-200/60 dark:border-emerald-800/40 rounded-md px-2.5 py-1.5 text-slate-700 dark:text-slate-300 transition-colors"
            >
              <div className="flex items-center gap-2 min-w-0 pr-2 rtl:pr-0 rtl:pl-2">
                <FileText className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" />
                <span className="font-medium truncate text-slate-800 dark:text-slate-200">
                  {cit.source_title}
                </span>
                {cit.page_number && (
                  <span className="bg-emerald-100 dark:bg-emerald-900/60 text-emerald-800 dark:text-emerald-300 text-[10px] px-1.5 py-0.5 rounded shrink-0 font-medium">
                    {t.page} {cit.page_number}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
