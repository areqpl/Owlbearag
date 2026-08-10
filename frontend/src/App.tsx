import { FC, useState, useEffect } from 'react';
import { Spinner } from './components/Spinner';
import { Toast } from './components/Toast';
import { ChatWindow } from './components/ChatWindow';
import { Message } from './components/ChatMessage';
import { DarkModeToggle } from './components/DarkModeToggle';
import { LanguageSwitcher } from './components/LanguageSwitcher';
import {
  GithubIcon,
  SettingsIcon,
  TrashIcon,
  SendIcon,
  LightbulbIcon,
  BoltIcon,
  BrainIcon,
} from './components/Icons';
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
      // Ignore quota error
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
        if (resp.status === 405) {
          setShowSettings(true); // Open settings bar automatically on 405
          throw new Error(getTranslation(lang, 'error405'));
        } else if (resp.status === 404) {
          throw new Error(getTranslation(lang, 'error404'));
        } else if (resp.status === 500) {
          throw new Error(getTranslation(lang, 'error500'));
        } else {
          throw new Error(`${getTranslation(lang, 'serverError')} (${resp.status})`);
        }
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
      let msg = getTranslation(lang, 'errorNetwork');
      if (err instanceof Error && err.message) {
        msg = err.message;
      }
      setError(msg);
      // Clean up empty assistant placeholder on failure
      setMessages((prev) => prev.filter((m) => m.content.length > 0));
    } finally {
      setLoading(false);
    }
  };

  const t = (key: string) => getTranslation(lang, key);

  return (
    <section className="flex h-screen flex-col bg-slate-50 text-slate-900 dark:bg-black dark:text-gray-100 transition-colors duration-200">
      {/* Header Bar */}
      <header className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-200 bg-white/90 px-4 py-3 backdrop-blur dark:bg-black/90 dark:border-gray-800 shadow-sm gap-2.5">
        <div className="flex items-center gap-3">
          <img src="/owl_icon.png" alt="Owlbearag Logo" className="h-8 w-8 object-contain flex-shrink-0" />
          <div>
            <h1 className="text-lg font-bold tracking-tight text-indigo-600 dark:text-indigo-400 leading-tight">
              {t('title')}
            </h1>
            <p className="text-[10px] text-slate-500 dark:text-gray-400 font-mono">{t('subtitle')}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
          <a
            href="https://github.com/areqpl/Owlbearag"
            target="_blank"
            rel="noreferrer"
            className="rounded-xl border border-slate-300 bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-200 dark:border-gray-800 dark:bg-black dark:text-gray-200 dark:hover:bg-gray-900 transition flex items-center gap-1.5 shadow-sm focus-visible:ring-2 focus-visible:ring-indigo-500"
            title="GitHub Repository"
          >
            <GithubIcon />
            <span className="hidden xs:inline">{t('github')}</span>
          </a>

          <button
            onClick={() => setShowSettings(!showSettings)}
            className={`rounded-xl border px-3 py-2 text-xs font-semibold transition flex items-center gap-1.5 shadow-sm focus-visible:ring-2 focus-visible:ring-indigo-500 ${
              showSettings
                ? 'border-indigo-500 bg-indigo-50 text-indigo-600 dark:border-indigo-600 dark:bg-indigo-950/40 dark:text-indigo-300'
                : 'border-slate-300 bg-slate-100 text-slate-700 hover:bg-slate-200 dark:border-gray-800 dark:bg-black dark:text-gray-200 dark:hover:bg-gray-900'
            }`}
            title="Configure API Endpoint"
          >
            <SettingsIcon />
            <span>API</span>
          </button>

          <LanguageSwitcher currentLanguage={lang} onLanguageChange={handleLanguageChange} />
          <DarkModeToggle />

          {messages.length > 0 && (
            <button
              onClick={handleClearChat}
              className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-600 hover:bg-red-100 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300 dark:hover:bg-red-900/60 transition flex items-center gap-1.5 shadow-sm focus-visible:ring-2 focus-visible:ring-red-500"
              title={t('clear')}
            >
              <TrashIcon />
              <span className="hidden sm:inline">{t('clear')}</span>
            </button>
          )}
        </div>
      </header>

      {/* Settings Panel Bar */}
      {showSettings && (
        <div className="border-b border-indigo-200 bg-indigo-50/90 px-4 py-3 text-xs dark:border-indigo-900/40 dark:bg-indigo-950/30 transition-all flex flex-col sm:flex-row items-start sm:items-center gap-2 animate-slide-down shadow-inner">
          <label htmlFor="apiBaseInput" className="font-semibold text-slate-700 dark:text-indigo-200 flex-shrink-0">
            ⚙️ {t('apiUrlLabel')}
          </label>
          <input
            id="apiBaseInput"
            type="text"
            value={apiBaseUrl}
            onChange={(e) => handleSaveApiBase(e.target.value)}
            placeholder="http://127.0.0.1:8000"
            className="w-full sm:flex-1 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-slate-800 placeholder-gray-400 focus:border-indigo-500 focus:outline-none dark:border-gray-800 dark:bg-black dark:text-gray-100 font-mono shadow-sm"
          />
        </div>
      )}

      {/* Empty State / Welcome Container */}
      {messages.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center p-6 text-center animate-fade-in">
          <div className="max-w-md w-full space-y-5">
            <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-100 p-3 dark:bg-indigo-950/80 border border-indigo-200 dark:border-indigo-800 shadow-md">
              <img src="/owl_icon.png" alt="Owlbearag Icon" className="h-full w-full object-contain" />
            </div>
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white">
                {t('welcomeTitle')}
              </h2>
              <p className="mt-1.5 text-xs sm:text-sm text-slate-600 dark:text-gray-400 leading-relaxed">
                {t('welcomeSub')}
              </p>
            </div>

            {/* Starter Prompt Chips */}
            <div className="pt-2 space-y-2.5 text-left">
              <button
                onClick={() => handleSelectChip(t('chip1'))}
                className="w-full rounded-2xl border border-slate-200 bg-white p-3.5 text-xs font-medium text-slate-700 hover:border-indigo-500 hover:bg-indigo-50/50 dark:border-gray-800 dark:bg-[#0a0a0a] dark:text-gray-200 dark:hover:border-indigo-600 dark:hover:bg-indigo-950/40 transition-all shadow-sm flex items-center justify-between group"
              >
                <div className="flex items-center gap-2.5">
                  <LightbulbIcon className="text-amber-500 flex-shrink-0" />
                  <span>{t('chip1')}</span>
                </div>
                <span className="text-indigo-500 font-bold group-hover:translate-x-1 transition-transform">→</span>
              </button>

              <button
                onClick={() => handleSelectChip(t('chip2'))}
                className="w-full rounded-2xl border border-slate-200 bg-white p-3.5 text-xs font-medium text-slate-700 hover:border-indigo-500 hover:bg-indigo-50/50 dark:border-gray-800 dark:bg-[#0a0a0a] dark:text-gray-200 dark:hover:border-indigo-600 dark:hover:bg-indigo-950/40 transition-all shadow-sm flex items-center justify-between group"
              >
                <div className="flex items-center gap-2.5">
                  <BoltIcon className="text-indigo-500 flex-shrink-0" />
                  <span>{t('chip2')}</span>
                </div>
                <span className="text-indigo-500 font-bold group-hover:translate-x-1 transition-transform">→</span>
              </button>

              <button
                onClick={() => handleSelectChip(t('chip3'))}
                className="w-full rounded-2xl border border-slate-200 bg-white p-3.5 text-xs font-medium text-slate-700 hover:border-indigo-500 hover:bg-indigo-50/50 dark:border-gray-800 dark:bg-[#0a0a0a] dark:text-gray-200 dark:hover:border-indigo-600 dark:hover:bg-indigo-950/40 transition-all shadow-sm flex items-center justify-between group"
              >
                <div className="flex items-center gap-2.5">
                  <BrainIcon className="text-purple-500 flex-shrink-0" />
                  <span>{t('chip3')}</span>
                </div>
                <span className="text-indigo-500 font-bold group-hover:translate-x-1 transition-transform">→</span>
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
        className="flex items-center gap-2.5 border-t border-slate-200 bg-white px-4 py-3 dark:bg-black dark:border-gray-800 shadow-lg"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t('placeholder')}
          className="flex-1 rounded-2xl border border-slate-300 bg-slate-50 px-4 py-3 text-sm text-slate-900 placeholder-slate-400 focus:border-indigo-500 focus:bg-white focus:outline-none dark:border-gray-800 dark:bg-[#0a0a0a] dark:text-white dark:placeholder-gray-500 shadow-inner transition-all"
          aria-label={t('placeholder')}
          disabled={loading}
        />
        <button
          type="submit"
          className="rounded-2xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white transition-all hover:bg-indigo-500 disabled:opacity-50 shadow-md flex items-center gap-2 focus-visible:ring-2 focus-visible:ring-indigo-500"
          disabled={loading || !input.trim()}
        >
          <SendIcon />
          <span className="hidden sm:inline">{t('send')}</span>
        </button>
      </form>

      {/* Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/40 backdrop-blur-[2px] z-40 animate-fade-in">
          <Spinner />
          <span className="mt-3 text-xs font-semibold text-indigo-300 tracking-wide">{t('thinking')}</span>
        </div>
      )}

      {/* Toast Exception Alert */}
      {error && <Toast message={error} onClose={() => setError(null)} />}
    </section>
  );
};

export default App;
