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

  const handleClearChat = () => {
    setMessages([]);
    localStorage.removeItem('owlbearag_chat_messages');
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

    try {
      const resp = await fetch('/query', {
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
      // Remove empty assistant placeholder on error
      setMessages((prev) => prev.filter((m) => m.content.length > 0));
    } finally {
      setLoading(false);
    }
  };

  const t = (key: string) => getTranslation(lang, key);

  return (
    <section className="flex h-screen flex-col bg-gray-900 text-gray-100 dark:bg-black transition-colors duration-200">
      {/* Header Bar */}
      <header className="flex flex-wrap items-center justify-between border-b border-gray-800 bg-gray-900/90 px-4 py-3 backdrop-blur dark:bg-black/90 dark:border-gray-800">
        <div className="flex items-center gap-2.5">
          <img src="/owl_icon.png" alt="Owlbearag Logo" className="h-7 w-7 object-contain" />
          <div>
            <h1 className="text-lg font-bold tracking-tight text-indigo-400 dark:text-indigo-300">
              {t('title')}
            </h1>
            <p className="text-[10px] text-gray-400 font-mono">{t('subtitle')}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 mt-2 sm:mt-0">
          <LanguageSwitcher currentLanguage={lang} onLanguageChange={handleLanguageChange} />
          <DarkModeToggle />
          {messages.length > 0 && (
            <button
              onClick={handleClearChat}
              className="rounded-lg border border-red-900/50 bg-red-950/30 px-2.5 py-1.5 text-xs font-semibold text-red-300 hover:bg-red-900/60 hover:text-white transition"
              title={t('clear')}
            >
              🗑️ {t('clear')}
            </button>
          )}
        </div>
      </header>

      {/* Main Chat Display */}
      <ChatWindow messages={messages} />

      {/* Input Form */}
      <form
        onSubmit={handleSubmit}
        className="flex items-center gap-2 border-t border-gray-800 bg-gray-900 px-4 py-3 dark:bg-black dark:border-gray-800"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t('placeholder')}
          className="flex-1 rounded-xl border border-gray-700 bg-gray-800 px-4 py-2.5 text-sm text-white placeholder-gray-400 focus:border-indigo-500 focus:outline-none dark:border-gray-800 dark:bg-[#111111]"
          aria-label={t('placeholder')}
          disabled={loading}
        />
        <button
          type="submit"
          className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-50 shadow-md"
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
