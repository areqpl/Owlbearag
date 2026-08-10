export type Language = 'en' | 'pl' | 'uk' | 'zh' | 'nl' | 'de';

export interface LanguageInfo {
  code: Language;
  name: string;
  flag: string;
}

export const LANGUAGES: LanguageInfo[] = [
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'pl', name: 'Polski', flag: '🇵🇱' },
  { code: 'uk', name: 'Українська', flag: '🇺🇦' },
  { code: 'zh', name: '中文', flag: '🇨🇳' },
  { code: 'nl', name: 'Nederlands', flag: '🇳🇱' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
];

export const translations: Record<Language, Record<string, string>> = {
  en: {
    title: 'Owlbearag RAG Chat',
    subtitle: 'Autonomous GPU Node',
    placeholder: 'Ask a question…',
    send: 'Send',
    clear: 'Clear Chat',
    error: 'Error',
    serverError: 'Server error',
    thinking: 'Thinking…',
    amoledDark: 'AMOLED Dark Mode',
    lightMode: 'Light Mode',
    language: 'Language',
  },
  pl: {
    title: 'Owlbearag Czat RAG',
    subtitle: 'Autonomiczny Węzeł GPU',
    placeholder: 'Zadaj pytanie…',
    send: 'Wyślij',
    clear: 'Wyczyść Czat',
    error: 'Błąd',
    serverError: 'Błąd serwera',
    thinking: 'Myślenie…',
    amoledDark: 'Tryb AMOLED Ciemny',
    lightMode: 'Tryb Jasny',
    language: 'Język',
  },
  uk: {
    title: 'Owlbearag Чат RAG',
    subtitle: 'Автономний Вузол GPU',
    placeholder: 'Поставте запитання…',
    send: 'Надіслати',
    clear: 'Очистити чат',
    error: 'Помилка',
    serverError: 'Помилка сервера',
    thinking: 'Думаю…',
    amoledDark: 'Темний режим AMOLED',
    lightMode: 'Світлий режим',
    language: 'Мова',
  },
  zh: {
    title: 'Owlbearag RAG 聊天',
    subtitle: '自主 GPU 节点',
    placeholder: '请输入问题…',
    send: '发送',
    clear: '清空对话',
    error: '错误',
    serverError: '服务器错误',
    thinking: '思考中…',
    amoledDark: 'AMOLED 纯黑模式',
    lightMode: '浅色模式',
    language: '语言',
  },
  nl: {
    title: 'Owlbearag RAG Chat',
    subtitle: 'Autonome GPU-node',
    placeholder: 'Stel een vraag…',
    send: 'Versturen',
    clear: 'Chat wissen',
    error: 'Fout',
    serverError: 'Serverfout',
    thinking: 'Denken…',
    amoledDark: 'AMOLED Donkere Modus',
    lightMode: 'Lichte Modus',
    language: 'Taal',
  },
  de: {
    title: 'Owlbearag RAG Chat',
    subtitle: 'Autonomer GPU-Knoten',
    placeholder: 'Stelle eine Frage…',
    send: 'Senden',
    clear: 'Chat leeren',
    error: 'Fehler',
    serverError: 'Serverfehler',
    thinking: 'Denken…',
    amoledDark: 'AMOLED Dunkelmodus',
    lightMode: 'Heller Modus',
    language: 'Sprache',
  },
};

export const getTranslation = (lang: Language, key: string): string => {
  return translations[lang]?.[key] ?? translations.en[key] ?? key;
};
