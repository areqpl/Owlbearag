import { FC, useEffect, useRef } from 'react';
import { ChatMessage, Message } from './ChatMessage';

type ChatWindowProps = {
  messages: Message[];
};

/**
 * Scrollable chat window container with auto-scroll to bottom.
 */
export const ChatWindow: FC<ChatWindowProps> = ({ messages }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-2" aria-live="polite">
      {messages.map((msg, idx) => (
        <ChatMessage
          key={idx}
          role={msg.role}
          content={msg.content}
          timestamp={msg.timestamp}
        />
      ))}
      <div ref={bottomRef} />
    </div>
  );
};
