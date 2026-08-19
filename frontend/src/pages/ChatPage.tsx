import React, { useState, useEffect, useRef, useCallback } from 'react';
import { apiClient } from '../api/client';
import { ConversationSidebar } from '../components/ConversationSidebar';
import type { ConversationItem } from '../components/ConversationSidebar';
import { MessageBubble } from '../components/MessageBubble';
import type { MessageItem } from '../components/MessageBubble';
import { MessageComposer } from '../components/MessageComposer';
import type { User } from '../state/authStore';
import type { Translations, Language, Theme } from '../i18n/translations';
import { ShieldAlert, Sparkles, MessageSquare, Menu } from 'lucide-react';

interface ChatPageProps {
  user: User | null;
  onLogout: () => void;
  t: Translations;
  lang: Language;
  onSetLang: (lang: Language) => void;
  theme: Theme;
  onSetTheme: (theme: Theme) => void;
}

export const ChatPage: React.FC<ChatPageProps> = ({
  user,
  onLogout,
  t,
  lang,
  onSetLang,
  theme,
  onSetTheme,
}) => {
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Fetch conversations list
  const fetchConversations = useCallback(async () => {
    try {
      const response = await apiClient.get('/conversations');
      const data = response.data.data || [];
      setConversations(data);
      if (data.length > 0 && !activeConversationId) {
        setActiveConversationId(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load conversations:', err);
    }
  }, [activeConversationId]);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  // Fetch messages for active conversation
  const fetchMessages = useCallback(async (conversationId: number) => {
    try {
      const response = await apiClient.get(`/conversations/${conversationId}/messages`);
      const data = response.data.data || [];
      setMessages(data);
    } catch (err) {
      console.error('Failed to load messages:', err);
    }
  }, []);

  useEffect(() => {
    if (activeConversationId) {
      setLoadingMessages(true);
      fetchMessages(activeConversationId).finally(() => setLoadingMessages(false));
    } else {
      setMessages([]);
    }
  }, [activeConversationId, fetchMessages]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Polling mechanism for pending messages
  const hasPendingMessage = messages.some((m) => m.status === 'pending');

  useEffect(() => {
    if (!hasPendingMessage || !activeConversationId) return;

    const intervalId = setInterval(() => {
      fetchMessages(activeConversationId);
    }, 2000);

    return () => clearInterval(intervalId);
  }, [hasPendingMessage, activeConversationId, fetchMessages]);

  // Create new conversation
  const handleNewConversation = async () => {
    try {
      const response = await apiClient.post('/conversations', {
        title: t.newConversation,
      });
      const newConv = response.data.data;
      setConversations((prev) => [newConv, ...prev]);
      setActiveConversationId(newConv.id);
      setMessages([]);
    } catch (err) {
      console.error('Failed to create conversation:', err);
    }
  };

  // Delete conversation
  const handleDeleteConversation = async (id: number) => {
    try {
      await apiClient.delete(`/conversations/${id}`);
      const updated = conversations.filter((c) => c.id !== id);
      setConversations(updated);
      if (activeConversationId === id) {
        setActiveConversationId(updated.length > 0 ? updated[0].id : null);
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  };

  // Send message
  const handleSendMessage = async (content: string) => {
    let targetConversationId = activeConversationId;

    // Auto-create conversation if none active
    if (!targetConversationId) {
      const convRes = await apiClient.post('/conversations', {
        title: content.slice(0, 40),
      });
      const created = convRes.data.data;
      targetConversationId = created.id;
      setConversations((prev) => [created, ...prev]);
      setActiveConversationId(created.id);
    }

    try {
      const response = await apiClient.post(
        `/conversations/${targetConversationId}/messages`,
        { content }
      );
      const { user_message, assistant_message } = response.data.data;

      setMessages((prev) => [...prev, user_message, assistant_message]);
      fetchConversations(); // refresh title if updated
    } catch (err: any) {
      console.error('Failed to send message:', err);
      alert(err.response?.data?.message || 'Failed to send question.');
    }
  };

  // Get active conversation title
  const activeConversation = conversations.find((c) => c.id === activeConversationId);

  // Find last user question for retry
  const lastUserMessage = [...messages].reverse().find((m) => m.role === 'user');

  return (
    <div className="flex h-full w-full max-h-screen overflow-hidden font-sans transition-colors bg-slate-50 dark:bg-slate-950">
      {/* Desktop Sidebar */}
      <div className="hidden lg:flex h-full shrink-0">
        <ConversationSidebar
          conversations={conversations}
          activeId={activeConversationId}
          onSelect={setActiveConversationId}
          onNew={handleNewConversation}
          onDelete={handleDeleteConversation}
          user={user}
          onLogout={onLogout}
          t={t}
          lang={lang}
          onSetLang={onSetLang}
          theme={theme}
          onSetTheme={onSetTheme}
        />
      </div>

      {/* Mobile Off-Canvas Sidebar Drawer */}
      {mobileSidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          {/* Backdrop */}
          <div
            onClick={() => setMobileSidebarOpen(false)}
            className="fixed inset-0 bg-slate-950/60 backdrop-blur-xs transition-opacity animate-fade-in"
          />

          {/* Drawer container */}
          <div className="relative z-50 flex h-full max-w-xs w-full shadow-2xl animate-slide-in">
            <ConversationSidebar
              conversations={conversations}
              activeId={activeConversationId}
              onSelect={setActiveConversationId}
              onNew={handleNewConversation}
              onDelete={handleDeleteConversation}
              user={user}
              onLogout={onLogout}
              t={t}
              lang={lang}
              onSetLang={onSetLang}
              theme={theme}
              onSetTheme={onSetTheme}
              onClose={() => setMobileSidebarOpen(false)}
            />
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col h-full min-w-0 min-h-0 bg-white dark:bg-slate-900 transition-colors overflow-hidden">
        {/* Top Clinical Header */}
        <header className="shrink-0 bg-white/90 dark:bg-slate-900/90 backdrop-blur-xs border-b border-slate-200 dark:border-slate-800 px-4 sm:px-6 py-3 flex items-center justify-between shadow-2xs transition-colors">
          <div className="flex items-center gap-3 min-w-0">
            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileSidebarOpen(true)}
              className="lg:hidden p-2 -ms-1 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition cursor-pointer"
              aria-label="Open navigation sidebar"
            >
              <Menu className="w-5 h-5" />
            </button>

            <div className="min-w-0">
              <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100 truncate">
                {activeConversation?.title || t.appSubtitle}
              </h2>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1 truncate">
                <span className="truncate">{t.appTagline}</span>
                <span>•</span>
                <span className="text-emerald-600 dark:text-emerald-400 font-semibold shrink-0">ADA / USPSTF</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0 ms-2">
            <div className="hidden md:flex items-center gap-1.5 bg-amber-50 dark:bg-amber-950/40 border border-amber-200/80 dark:border-amber-800/60 text-amber-800 dark:text-amber-300 text-[11px] px-2.5 py-1 rounded-md font-medium">
              <ShieldAlert className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 shrink-0" />
              <span>{t.scopeWarning}</span>
            </div>
          </div>
        </header>

        {/* Message Thread (Internal vertical scrolling only) */}
        <div className="flex-1 min-h-0 overflow-y-auto p-3 sm:p-6 space-y-2 chat-scrollbar">
          {messages.length === 0 && !loadingMessages ? (
            <div className="max-w-xl mx-auto my-8 sm:my-12 text-center space-y-6 px-2">
              <div className="w-12 h-12 rounded-2xl bg-emerald-100 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-400 flex items-center justify-center mx-auto shadow-xs">
                <Sparkles className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">
                  {t.emptyStateTitle}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-md mx-auto leading-relaxed">
                  {t.emptyStateSubtitle}
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-left rtl:text-right pt-2">
                {[
                  t.samplePrompt1,
                  t.samplePrompt2,
                  t.samplePrompt3,
                  t.samplePrompt4,
                ].map((promptText, i) => (
                  <button
                    key={i}
                    onClick={() => handleSendMessage(promptText)}
                    className="p-3 bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 hover:border-emerald-500 dark:hover:border-emerald-400 rounded-xl text-xs text-slate-700 dark:text-slate-200 hover:text-emerald-800 dark:hover:text-emerald-300 transition shadow-2xs hover:shadow-xs text-left rtl:text-right cursor-pointer flex items-start gap-2"
                  >
                    <MessageSquare className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                    <span>{promptText}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto">
              {messages.map((msg) => (
                <MessageBubble
                  key={msg.id}
                  message={msg}
                  lastUserMessageContent={lastUserMessage?.content || ''}
                  onRetry={(text) => handleSendMessage(text)}
                  t={t}
                />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Message Composer (Fixed at bottom of flex column) */}
        <MessageComposer
          onSendMessage={handleSendMessage}
          disabled={hasPendingMessage}
          t={t}
        />
      </main>
    </div>
  );
};
