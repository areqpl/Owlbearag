import { FC, useEffect } from 'react';
import { AlertTriangleIcon, CloseIcon } from './Icons';

interface ToastProps {
  message: string;
  onClose: () => void;
  duration?: number;
}

export const Toast: FC<ToastProps> = ({ message, onClose, duration = 6000 }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, duration);
    return () => clearTimeout(timer);
  }, [onClose, duration]);

  return (
    <div
      className="fixed bottom-20 right-4 left-4 sm:left-auto z-50 flex items-center justify-between gap-3 max-w-md rounded-xl bg-red-600 px-4 py-3 text-sm font-medium text-white shadow-2xl animate-slide-down border border-red-500"
      role="alert"
    >
      <div className="flex items-center gap-2.5">
        <AlertTriangleIcon className="flex-shrink-0 text-white" />
        <span className="leading-snug">{message}</span>
      </div>
      <button
        onClick={onClose}
        className="flex h-7 w-7 items-center justify-center rounded-lg hover:bg-red-700 text-white/80 hover:text-white transition flex-shrink-0"
        aria-label="Dismiss error"
      >
        <CloseIcon />
      </button>
    </div>
  );
};
