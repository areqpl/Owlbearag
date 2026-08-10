import { FC, useEffect, useState } from 'react';

export const DarkModeToggle: FC = () => {
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem('owlbearag_theme');
    if (saved) return saved === 'dark';
    return true; // Default to dark/AMOLED
  });

  useEffect(() => {
    const root = document.documentElement;
    if (isDark) {
      root.classList.add('dark');
      localStorage.setItem('owlbearag_theme', 'dark');
    } else {
      root.classList.remove('dark');
      localStorage.setItem('owlbearag_theme', 'light');
    }
  }, [isDark]);

  return (
    <button
      onClick={() => setIsDark((prev) => !prev)}
      className="flex items-center gap-1 rounded-lg border border-gray-700 bg-gray-800 px-2.5 py-1.5 text-xs font-semibold text-gray-200 shadow-sm transition hover:bg-gray-700 hover:text-white dark:border-gray-800 dark:bg-black dark:hover:bg-gray-900"
      title="Toggle AMOLED Dark Mode"
      aria-label="Toggle AMOLED Dark Mode"
    >
      <span>{isDark ? '🌙 AMOLED' : '☀️ Light'}</span>
    </button>
  );
};
