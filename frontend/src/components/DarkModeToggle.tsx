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
      className="flex items-center gap-1 rounded-lg border border-slate-300 bg-slate-100 px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-200 dark:border-gray-800 dark:bg-black dark:text-gray-200 dark:hover:bg-gray-900 transition shadow-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
      title="Toggle AMOLED Dark / Light Mode"
      aria-label="Toggle AMOLED Dark / Light Mode"
    >
      <span>{isDark ? '🌙 AMOLED' : '☀️ Light'}</span>
    </button>
  );
};
