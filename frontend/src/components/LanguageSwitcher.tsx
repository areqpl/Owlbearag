import { FC } from 'react';
import { Language, LANGUAGES } from '../i18n';

interface Props {
  currentLanguage: Language;
  onLanguageChange: (lang: Language) => void;
}

export const LanguageSwitcher: FC<Props> = ({ currentLanguage, onLanguageChange }) => {
  return (
    <div className="flex items-center gap-1">
      <select
        value={currentLanguage}
        onChange={(e) => onLanguageChange(e.target.value as Language)}
        className="rounded-lg border border-slate-300 bg-slate-100 px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-200 dark:border-gray-800 dark:bg-black dark:text-gray-100 dark:hover:bg-gray-900 transition shadow-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
        aria-label="Select language"
      >
        {LANGUAGES.map((lang) => (
          <option key={lang.code} value={lang.code}>
            {lang.flag} {lang.name}
          </option>
        ))}
      </select>
    </div>
  );
};
