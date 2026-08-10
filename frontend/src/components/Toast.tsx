import { FC, useEffect } from 'react';

interface ToastProps {
  message: string;
  onClose: () => void;
  duration?: number;
}

export const Toast: FC<ToastProps> = ({ message, onClose, duration = 4000 }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, duration);
    return () => clearTimeout(timer);
  }, [onClose, duration]);

  return (
    <div
      className="fixed bottom-20 right-4 z-50 flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2.5 text-sm font-medium text-white shadow-lg transition-all"
      role="alert"
    >
      <span>⚠️ {message}</span>
      <button
        onClick={onClose}
        className="ml-2 text-white/80 hover:text-white"
        aria-label="Dismiss error"
      >
        ✕
      </button>
    </div>
  );
};
