import { FC, useState, useEffect } from 'react';
import { Spinner } from './components/Spinner';
import { Toast } from './components/Toast';
import { ChatWindow } from './components/ChatWindow';
import { Message } from './components/ChatMessage';
import { DarkModeToggle } from './components/DarkModeToggle';
import { LanguageSwitcher } from './components/LanguageSwitcher';
import { Language, getTranslation } from './i18n';

export const App: FC = () => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>(() => {
    try {
      const saved = localStorage.getItem('owlbearag_chat_messages');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [lang, setLang] = useState<Language>(() => {
    const saved = localStorage.getItem('owlbearag_lang') as Language;
    return saved || 'en';
  });

  const [apiBaseUrl, setApiBaseUrl] = useState<string>(() => {
    return localStorage.getItem('owlbearag_api_base') || import.meta.env.VITE_API_BASE_URL || '';
  });

  const [showSettings, setShowSettings] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      localStorage.setItem('owlbearag_chat_messages', JSON.stringify(messages));
    } catch {
      // Ignore storage quota error
    }
  }, [messages]);

  const handleLanguageChange = (newLang: Language) => {
    setLang(newLang);
    localStorage.setItem('owlbearag_lang', newLang);
  };

  const handleSaveApiBase = (url: string) => {
    setApiBaseUrl(url);
    localStorage.setItem('owlbearag_api_base', url);
  };

  const handleClearChat = () => {
    setMessages([]);
    localStorage.removeItem('owlbearag_chat_messages');
  };

  const handleSelectChip = (promptText: string) => {
    setInput(promptText);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    const userMessage: Message = {
      role: 'user',
      content: trimmed,
      timestamp: Date.now(),
    };

    const assistantPlaceholder: Message = {
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage, assistantPlaceholder]);
    setInput('');
    setLoading(true);
    setError(null);

    const targetUrl = apiBaseUrl ? `${apiBaseUrl.replace(/\/$/, '')}/query` : '/query';

    try {
      const resp = await fetch(targetUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: trimmed, stream: true }),
      });

      if (!resp.ok) {
        throw new Error(`${getTranslation(lang, 'serverError')} ${resp.status}`);
      }

      if (resp.body && resp.headers.get('content-type')?.includes('text/plain')) {
        const reader = resp.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let accumulated = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value, { stream: true });
          accumulated += chunk;

          setMessages((prev) => {
            const next = [...prev];
            next[next.length - 1] = {
              ...next[next.length - 1],
              content: accumulated,
            };
            return next;
          });
        }
      } else {
        const data = await resp.json();
        const responseText = data.response || data.answer || '';
        setMessages((prev) => {
          const next = [...prev];
          next[next.length - 1] = {
            ...next[next.length - 1],
            content: responseText,
          };
          return next;
        });
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : getTranslation(lang, 'serverError');
      setError(msg);
      // Remove empty placeholder on error
      setMessages((prev) => prev.filter((m) => m.content.length > 0));
    } finally {
      setLoading(false);
    }
  };

  const t = (key: string) => getTranslation(lang, key);

  return (
    <section className="flex h-screen flex-col bg-slate-50 text-slate-900 dark:bg-black dark:text-gray-100 transition-colors duration-200">
      {/* Header Bar */}
      <header className="flex flex-wrap items-center justify-between border-b border-slate-200 bg-white/90 px-4 py-3 backdrop-blur dark:bg-black/90 dark:border-gray-800 shadow-sm">
        <div className="flex items-center gap-2.5">
          <img src="/owl_icon.png" alt="Owlbearag Logo" className="h-8 w-8 object-contain" />
          <div>
            <h1 className="text-lg font-bold tracking-tight text-indigo-600 dark:text-indigo-400">
              {t('title')}
            </h1>
            <p className="text-[10px] text-slate-500 dark:text-gray-400 font-mono">{t('subtitle')}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 mt-2 sm:mt-0 flex-wrap">
          <a
            href="https://github.com/areqpl/Owlbearag"
            target="_blank"
            rel="noreferrer"
            className="rounded-lg border border-slate-300 bg-slate-100 px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-200 dark:border-gray-800 dark:bg-black dark:text-gray-200 dark:hover:bg-gray-900 transition flex items-center gap-1 shadow-sm"
            title="GitHub Repository"
          >
            ⭐ {t('github')}
          </a>

          <button
            onClick={() => setShowSettings(!showSettings)}
            className="rounded-lg border border-slate-300 bg-slate-100 px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-200 dark:border-gray-800 dark:bg-black dark:text-gray-200 dark:hover:bg-gray-900 transition shadow-sm"
            title="Configure API Endpoint"
          >
            ⚙️ API
          </button>

          <LanguageSwitcher currentLanguage={lang} onLanguageChange={handleLanguageChange} />
          <DarkModeToggle />

          {messages.length > 0 && (
            <button
              onClick={handleClearChat}
              className="rounded-lg border border-red-200 bg-red-50 px-2.5 py-1.5 text-xs font-semibold text-red-600 hover:bg-red-100 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300 dark:hover:bg-red-900/60 transition shadow-sm"
              title={t('clear')}
            >
              🗑️ {t('clear')}
            </button>
          )}
        </div>
      </header>

      {/* Settings Modal Bar (if toggled) */}
      {showSettings && (
        <div className="border-b border-indigo-200 bg-indigo-50/80 px-4 py-2.5 text-xs dark:border-indigo-900/40 dark:bg-indigo-950/20 transition-all flex items-center gap-2">
          <label htmlFor="apiBaseInput" className="font-medium text-slate-700 dark:text-gray-300">
            {t('apiUrlLabel')}
          </label>
          <input
            id="apiBaseInput"
            type="text"
            value={apiBaseUrl}
            onChange={(e) => handleSaveApiBase(e.target.value)}
            placeholder="http://127.0.0.1:8000"
            className="flex-1 rounded border border-slate-300 bg-white px-2.5 py-1 text-slate-800 placeholder-gray-400 focus:border-indigo-500 focus:outline-none dark:border-gray-800 dark:bg-black dark:text-gray-100"
          />
        </div>
      )}

      {/* Empty State / Welcome Container */}
      {messages.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
          <div className="max-w-md space-y-4">
            <div className="inline-flex h-16 w-16 items-center justify-center rounded-full bg-indigo-100 p-2.5 dark:bg-indigo-950/80 border border-indigo-200 dark:border-indigo-800 shadow-md">
              <img src="/owl_icon.png" alt="Owlbearag Icon" className="h-full w-full object-contain" />
            </div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">
              {t('welcomeTitle')}
            </h2>
            <p className="text-xs text-slate-600 dark:text-gray-400 leading-relaxed">
              {t('welcomeSub')}
            </p>

            {/* Starter Prompt Chips */}
            <div className="pt-2 flex flex-col gap-2">
              <button
                onClick={() => handleSelectChip(t('chip1'))}
                className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-medium text-slate-700 hover:border-indigo-400 hover:bg-indigo-50/50 dark:border-gray-800 dark:bg-[#111111] dark:text-gray-200 dark:hover:border-indigo-600 dark:hover:bg-indigo-950/30 transition text-left shadow-sm flex items-center justify-between"
              >
                <span>💡 {t('chip1')}</span>
                <span className="text-indigo-500 font-bold">→</span>
              </button>
              <button
                onClick={() => handleSelectChip(t('chip2'))}
                className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-medium text-slate-700 hover:border-indigo-400 hover:bg-indigo-50/50 dark:border-gray-800 dark:bg-[#111111] dark:text-gray-200 dark:hover:border-indigo-600 dark:hover:bg-indigo-950/30 transition text-left shadow-sm flex items-center justify-between"
              >
                <span>⚡ {t('chip2')}</span>
                <span className="text-indigo-500 font-bold">→</span>
              </button>
              <button
                onClick={() => handleSelectChip(t('chip3'))}
                className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-medium text-slate-700 hover:border-indigo-400 hover:bg-indigo-50/50 dark:border-gray-800 dark:bg-[#111111] dark:text-gray-200 dark:hover:border-indigo-600 dark:hover:bg-indigo-950/30 transition text-left shadow-sm flex items-center justify-between"
              >
                <span>🧠 {t('chip3')}</span>
                <span className="text-indigo-500 font-bold">→</span>
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* Main Chat Window */
        <ChatWindow messages={messages} />
      )}

      {/* Input Form */}
      <form
        onSubmit={handleSubmit}
        className="flex items-center gap-2 border-t border-slate-200 bg-white px-4 py-3 dark:bg-black dark:border-gray-800 shadow-lg"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t('placeholder')}
          className="flex-1 rounded-xl border border-slate-300 bg-slate-50 px-4 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:border-indigo-500 focus:bg-white focus:outline-none dark:border-gray-800 dark:bg-[#111111] dark:text-white dark:placeholder-gray-500 shadow-inner"
          aria-label={t('placeholder')}
          disabled={loading}
        />
        <button
          type="submit"
          className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-50 shadow-md focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          disabled={loading || !input.trim()}
        >
          {t('send')}
        </button>
      </form>

      {/* Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/40 backdrop-blur-[2px]">
          <Spinner />
          <span className="mt-2 text-xs font-medium text-indigo-300">{t('thinking')}</span>
        </div>
      )}

      {/* Toast Error Alert */}
      {error && <Toast message={error} onClose={() => setError(null)} />}
    </section>
  );
};

export default App;
