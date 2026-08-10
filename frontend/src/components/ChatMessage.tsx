import { FC } from 'react';

export type Message = {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: number;
};

/**
 * Chat bubble supporting Light Mode, AMOLED Dark Mode, and standard dark theme.
 */
export const ChatMessage: FC<Message> = ({ role, content, timestamp }) => {
  if (!content) return null;
  const isUser = role === 'user';
  const containerClasses =
    `flex w-full mb-3 items-start gap-2.5 ` +
    (isUser ? 'justify-end' : 'justify-start');
  const bubbleClasses =
    `max-w-[85%] sm:max-w-md px-4 py-2.5 rounded-2xl break-words text-sm leading-relaxed shadow-sm transition-colors ` +
    (isUser
      ? 'bg-indigo-600 text-white rounded-tr-none'
      : 'bg-white text-slate-800 border border-slate-200 dark:bg-[#111111] dark:text-gray-100 dark:border-gray-800 rounded-tl-none');
  const timeStr = new Date(timestamp || Date.now()).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className={containerClasses}>
      {!isUser && (
        <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-indigo-100 dark:bg-indigo-950 p-1 border border-indigo-200 dark:border-indigo-700/50 shadow-sm">
          <img src="/owl_icon.png" alt="Owl Assistant Avatar" className="h-full w-full object-contain" />
        </div>
      )}
      <div
        className={bubbleClasses}
        role={isUser ? undefined : 'status'}
        aria-live={isUser ? undefined : 'polite'}
      >
        <div className="whitespace-pre-wrap">{content}</div>
        <div className="mt-1 text-[10px] opacity-60 text-right">{timeStr}</div>
      </div>
      {isUser && (
        <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-indigo-600 font-bold text-xs text-white shadow-sm" aria-hidden="true">
          👤
        </div>
      )}
    </div>
  );
};
