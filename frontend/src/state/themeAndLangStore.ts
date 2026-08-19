import { useState, useEffect, useMemo } from 'react';
import { translations } from '../i18n/translations';
import type { Language, Theme, Translations } from '../i18n/translations';

export function useThemeAndLang() {
  const [lang, setLangState] = useState<Language>(() => {
    const saved = localStorage.getItem('mrag_lang') as Language;
    return saved === 'ar' ? 'ar' : 'en';
  });

  const [theme, setThemeState] = useState<Theme>(() => {
    const saved = localStorage.getItem('mrag_theme') as Theme;
    return saved === 'light' || saved === 'dark' || saved === 'system' ? saved : 'system';
  });

  // Apply language and direction
  useEffect(() => {
    localStorage.setItem('mrag_lang', lang);
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
  }, [lang]);

  // Apply theme class to <html>
  useEffect(() => {
    localStorage.setItem('mrag_theme', theme);

    const root = document.documentElement;
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const applyTheme = () => {
      const isDark = theme === 'dark' || (theme === 'system' && mediaQuery.matches);
      if (isDark) {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    };

    applyTheme();

    const listener = () => {
      if (theme === 'system') {
        applyTheme();
      }
    };

    mediaQuery.addEventListener('change', listener);
    return () => mediaQuery.removeEventListener('change', listener);
  }, [theme]);

  const t: Translations = useMemo(() => translations[lang], [lang]);

  const setLang = (newLang: Language) => {
    setLangState(newLang);
  };

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
  };

  return {
    lang,
    setLang,
    theme,
    setTheme,
    t,
  };
}
