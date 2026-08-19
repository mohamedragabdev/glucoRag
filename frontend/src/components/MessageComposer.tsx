import React, { useState } from 'react';
import { Send, AlertCircle } from 'lucide-react';
import type { Translations } from '../i18n/translations';

interface MessageComposerProps {
  onSendMessage: (content: string) => Promise<void>;
  disabled: boolean;
  t: Translations;
}

export const MessageComposer: React.FC<MessageComposerProps> = ({
  onSendMessage,
  disabled,
  t,
}) => {
  const [content, setContent] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = content.trim();
    if (!trimmed || disabled || submitting) return;

    setSubmitting(true);
    try {
      await onSendMessage(trimmed);
      setContent('');
    } finally {
      setSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const charCount = content.length;
  const isOverLimit = charCount > 2000;

  return (
    <div className="shrink-0 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 p-4 transition-colors">
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto space-y-2">
        <div className="relative border border-slate-300 dark:border-slate-700 rounded-xl focus-within:ring-2 focus-within:ring-emerald-500 focus-within:border-emerald-500 bg-white dark:bg-slate-950 transition shadow-xs">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled || submitting}
            placeholder={
              disabled
                ? t.composerPendingPlaceholder
                : t.composerPlaceholder
            }
            rows={2}
            className="w-full resize-none px-4 py-3 text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-hidden disabled:bg-slate-50 dark:disabled:bg-slate-900 disabled:text-slate-400 rounded-xl bg-transparent"
          />

          <div className="flex items-center justify-between px-3 pb-2 pt-1 border-t border-slate-100 dark:border-slate-800/80">
            <div className="flex items-center gap-1.5 text-[11px] text-slate-400 dark:text-slate-500">
              {isOverLimit ? (
                <span className="text-rose-600 dark:text-rose-400 font-medium flex items-center gap-1">
                  <AlertCircle className="w-3.5 h-3.5" />
                  {charCount}/2000 {t.chars} ({t.charLimitExceeded})
                </span>
              ) : (
                <span>{charCount}/2000 {t.chars}</span>
              )}
            </div>

            <button
              type="submit"
              disabled={!content.trim() || disabled || submitting || isOverLimit}
              className="inline-flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-600 disabled:bg-slate-300 dark:disabled:bg-slate-800 text-white dark:text-slate-950 text-xs font-semibold px-4 py-2 rounded-lg transition shadow-xs cursor-pointer disabled:cursor-not-allowed"
            >
              <Send className="w-3.5 h-3.5 rtl:rotate-180" />
              <span>{t.sendQuestion}</span>
            </button>
          </div>
        </div>

        <p className="text-[11px] text-slate-400 dark:text-slate-500 text-center">
          {t.footerDisclaimer}
        </p>
      </form>
    </div>
  );
};
