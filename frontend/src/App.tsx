import { useState } from 'react';
import { useAuth } from './state/authStore';
import { useThemeAndLang } from './state/themeAndLangStore';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { ChatPage } from './pages/ChatPage';

export function App() {
  const { user, isAuthenticated, loading, login, register, logout } = useAuth();
  const { t, lang, setLang, theme, setTheme } = useThemeAndLang();
  const [authView, setAuthView] = useState<'login' | 'register'>('login');

  if (!isAuthenticated) {
    if (authView === 'register') {
      return (
        <RegisterPage
          onRegister={register}
          onNavigateToLogin={() => setAuthView('login')}
          loading={loading}
          t={t}
          lang={lang}
          onSetLang={setLang}
          theme={theme}
          onSetTheme={setTheme}
        />
      );
    }
    return (
      <LoginPage
        onLogin={login}
        onNavigateToRegister={() => setAuthView('register')}
        loading={loading}
        t={t}
        lang={lang}
        onSetLang={setLang}
        theme={theme}
        onSetTheme={setTheme}
      />
    );
  }

  return (
    <ChatPage
      user={user}
      onLogout={logout}
      t={t}
      lang={lang}
      onSetLang={setLang}
      theme={theme}
      onSetTheme={setTheme}
    />
  );
}

export default App;
