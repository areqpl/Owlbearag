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
        className="rounded-lg border border-gray-700 bg-gray-800 px-2.5 py-1.5 text-xs font-semibold text-gray-200 shadow-sm focus:border-indigo-500 focus:outline-none dark:border-gray-800 dark:bg-black dark:text-gray-100"
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
