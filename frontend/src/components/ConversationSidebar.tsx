import React from 'react';
import { Plus, MessageSquare, Trash2, LogOut, Activity, Stethoscope, Sun, Moon, Monitor, Languages, X } from 'lucide-react';
import type { User } from '../state/authStore';
import type { Translations, Language, Theme } from '../i18n/translations';

export interface ConversationItem {
  id: number;
  title: string | null;
  created_at: string;
  updated_at: string;
}

interface ConversationSidebarProps {
  conversations: ConversationItem[];
  activeId: number | null;
  onSelect: (id: number) => void;
  onNew: () => void;
  onDelete: (id: number) => void;
  user: User | null;
  onLogout: () => void;
  t: Translations;
  lang: Language;
  onSetLang: (lang: Language) => void;
  theme: Theme;
  onSetTheme: (theme: Theme) => void;
  onClose?: () => void;
}

export const ConversationSidebar: React.FC<ConversationSidebarProps> = ({
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
  user,
  onLogout,
  t,
  lang,
  onSetLang,
  theme,
  onSetTheme,
  onClose,
}) => {
  const handleSelect = (id: number) => {
    onSelect(id);
    if (onClose) onClose();
  };

  const handleNew = () => {
    onNew();
    if (onClose) onClose();
  };

  return (
    <aside className="w-72 bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-200 flex flex-col h-full max-h-full min-h-0 border-r border-slate-200 dark:border-slate-800 shrink-0 transition-colors overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-950 shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center text-slate-950 font-bold shadow-xs">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-semibold text-sm text-slate-900 dark:text-white tracking-tight">
                {t.appTitle}
              </h1>
              <p className="text-[10px] text-emerald-600 dark:text-emerald-400 font-medium">
                {t.appSubtitle}
              </p>
            </div>
          </div>

          {onClose && (
            <button
              onClick={onClose}
              className="lg:hidden p-1.5 text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-slate-800 rounded-lg transition cursor-pointer"
              aria-label="Close sidebar"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        <button
          onClick={handleNew}
          className="mt-4 w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-400 text-white dark:text-slate-950 text-xs font-semibold py-2 px-3 rounded-lg transition shadow-xs cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>{t.newConversation}</span>
        </button>
      </div>

      {/* Conversation list (Internal vertical scrolling only) */}
      <div className="flex-1 min-h-0 overflow-y-auto p-2 space-y-1 chat-scrollbar">
        <div className="px-2 py-1 text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
          {t.conversations}
        </div>

        {conversations.length === 0 ? (
          <div className="px-3 py-6 text-center text-xs text-slate-400 dark:text-slate-500">
            {t.noConversations}
          </div>
        ) : (
          conversations.map((conv) => {
            const isActive = conv.id === activeId;
            return (
              <div
                key={conv.id}
                onClick={() => handleSelect(conv.id)}
                className={`group flex items-center justify-between px-3 py-2 rounded-lg text-xs cursor-pointer transition ${
                  isActive
                    ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-900 dark:text-emerald-300 font-semibold border border-emerald-200/80 dark:border-emerald-800/60 shadow-2xs'
                    : 'text-slate-600 dark:text-slate-300 hover:bg-slate-200/70 dark:hover:bg-slate-900/60 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <div className="flex items-center gap-2.5 min-w-0 pr-2 rtl:pr-0 rtl:pl-2">
                  <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400 dark:text-slate-500'}`} />
                  <span className="truncate">{conv.title || 'New Conversation'}</span>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirm(t.deleteConfirm)) {
                      onDelete(conv.id);
                    }
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 transition cursor-pointer"
                  title={t.deleteTitle}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* Controls: Theme & Language */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-slate-100/70 dark:bg-slate-950/40 flex items-center justify-between text-xs text-slate-600 dark:text-slate-400 shrink-0">
        <div className="flex items-center gap-1">
          <Languages className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
          <button
            onClick={() => onSetLang(lang === 'en' ? 'ar' : 'en')}
            className="px-2 py-1 rounded-md bg-white hover:bg-slate-200/80 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-medium transition cursor-pointer text-[11px] border border-slate-200 dark:border-slate-700 shadow-2xs"
          >
            {lang === 'en' ? 'العربية' : 'English'}
          </button>
        </div>

        <div className="flex items-center gap-1 bg-slate-200 dark:bg-slate-800 rounded-lg p-0.5 border border-slate-300 dark:border-slate-700">
          <button
            onClick={() => onSetTheme('light')}
            title={t.lightMode}
            className={`p-1 rounded-md transition cursor-pointer ${theme === 'light' ? 'bg-white dark:bg-slate-700 text-amber-500 shadow-2xs' : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'}`}
          >
            <Sun className="w-3 h-3" />
          </button>
          <button
            onClick={() => onSetTheme('dark')}
            title={t.darkMode}
            className={`p-1 rounded-md transition cursor-pointer ${theme === 'dark' ? 'bg-white dark:bg-slate-700 text-blue-500 shadow-2xs' : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'}`}
          >
            <Moon className="w-3 h-3" />
          </button>
          <button
            onClick={() => onSetTheme('system')}
            title={t.systemMode}
            className={`p-1 rounded-md transition cursor-pointer ${theme === 'system' ? 'bg-white dark:bg-slate-700 text-emerald-600 dark:text-emerald-400 shadow-2xs' : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'}`}
          >
            <Monitor className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* User Profile & Logout */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-950/70 shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 min-w-0">
            <div className="w-7 h-7 rounded-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center text-slate-600 dark:text-slate-300 shrink-0">
              <Stethoscope className="w-3.5 h-3.5" />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium text-slate-900 dark:text-slate-200 truncate">{user?.name || t.clinicianRole}</p>
              <p className="text-[10px] text-slate-500 dark:text-slate-400 truncate">{user?.email}</p>
            </div>
          </div>

          <button
            onClick={onLogout}
            title={t.logout}
            className="p-1.5 text-slate-500 dark:text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-md transition cursor-pointer"
          >
            <LogOut className="w-4 h-4 rtl:rotate-180" />
          </button>
        </div>
      </div>
    </aside>
  );
};
