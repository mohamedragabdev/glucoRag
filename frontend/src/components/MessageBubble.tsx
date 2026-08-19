import React from 'react';
import { Bot, User, AlertCircle, RefreshCw, Clock } from 'lucide-react';
import { CitationList } from './CitationList';
import type { Citation } from './CitationList';
import type { Translations } from '../i18n/translations';

export interface MessageItem {
  id: number;
  conversation_id: number;
  role: 'user' | 'assistant';
  content: string | null;
  status: 'pending' | 'completed' | 'failed';
  error_message?: string | null;
  created_at: string;
  citations?: Citation[];
}

interface MessageBubbleProps {
  message: MessageItem;
  onRetry?: (originalQuestion: string) => void;
  lastUserMessageContent?: string;
  t: Translations;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  onRetry,
  lastUserMessageContent,
  t,
}) => {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex items-start justify-end gap-3 my-3">
        <div className="bg-blue-600 dark:bg-blue-700 text-white rounded-2xl rounded-tr-none rtl:rounded-tr-2xl rtl:rounded-tl-none px-4 py-3 max-w-[80%] shadow-xs">
          <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
          <div className="text-[10px] text-blue-200 mt-1 text-right rtl:text-left">
            {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>
        <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 flex items-center justify-center text-blue-700 dark:text-blue-300 shrink-0 shadow-xs">
          <User className="w-4 h-4" />
        </div>
      </div>
    );
  }

  // Assistant Message
  return (
    <div className="flex items-start gap-3 my-4">
      <div className="w-8 h-8 rounded-full bg-emerald-600 dark:bg-emerald-500 flex items-center justify-center text-white dark:text-slate-950 shrink-0 shadow-xs mt-0.5 font-bold">
        <Bot className="w-4 h-4" />
      </div>

      <div className="flex-1 max-w-[85%] bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl rounded-tl-none rtl:rounded-tl-2xl rtl:rounded-tr-none p-4 shadow-xs transition-colors">
        {message.status === 'pending' && (
          <div className="flex items-center gap-3 py-2 text-slate-500 dark:text-slate-400 text-sm">
            <div className="flex space-x-1.5 rtl:space-x-reverse">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce"></div>
            </div>
            <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
              {t.processingMessage}
            </span>
          </div>
        )}

        {message.status === 'failed' && (
          <div className="text-sm">
            <div className="flex items-center gap-2 text-rose-600 dark:text-rose-400 font-medium mb-1">
              <AlertCircle className="w-4 h-4" />
              <span>{t.processingFailedTitle}</span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-300 mb-3">
              {message.error_message || t.processingFailedDefault}
            </p>
            {onRetry && lastUserMessageContent && (
              <button
                onClick={() => onRetry(lastUserMessageContent)}
                className="inline-flex items-center gap-1.5 text-xs bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-medium px-3 py-1.5 rounded-md border border-slate-300 dark:border-slate-700 transition cursor-pointer"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>{t.retryQuestion}</span>
              </button>
            )}
          </div>
        )}

        {message.status === 'completed' && (
          <div>
            <div className="text-sm text-slate-800 dark:text-slate-100 whitespace-pre-wrap leading-relaxed">
              {message.content}
            </div>

            {message.citations && message.citations.length > 0 && (
              <CitationList citations={message.citations} t={t} />
            )}

            <div className="flex items-center justify-between mt-2 pt-2 text-[10px] text-slate-400 dark:text-slate-500">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
              <span className="text-[9px] uppercase tracking-wider font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-1.5 py-0.5 rounded border border-emerald-100 dark:border-emerald-800/40">
                {t.screeningAssistantBadge}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
