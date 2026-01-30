'use client';

import { cn } from '@/lib/utils';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date;
  isLoading?: boolean;
  sources?: string[];
  mcp?: string;
}

export function ChatMessage({ 
  role, 
  content, 
  timestamp, 
  isLoading,
  sources,
  mcp,
}: ChatMessageProps) {
  const isUser = role === 'user';

  return (
    <div className={cn(
      'flex gap-3 animate-slide-up',
      isUser && 'flex-row-reverse'
    )}>
      {/* Avatar */}
      <div className={cn(
        'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
        isUser 
          ? 'bg-primary-500 text-white' 
          : 'bg-gray-100 text-gray-600'
      )}>
        {isUser ? (
          <UserIcon className="w-4 h-4" />
        ) : (
          <BotIcon className="w-4 h-4" />
        )}
      </div>

      {/* Message */}
      <div className={cn(
        'max-w-[75%] rounded-2xl px-4 py-3',
        isUser 
          ? 'bg-primary-500 text-white rounded-br-md' 
          : 'bg-white border border-gray-100 shadow-card rounded-bl-md'
      )}>
        {isLoading ? (
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 bg-gray-300 rounded-full animate-pulse" />
            <span className="w-2 h-2 bg-gray-300 rounded-full animate-pulse [animation-delay:150ms]" />
            <span className="w-2 h-2 bg-gray-300 rounded-full animate-pulse [animation-delay:300ms]" />
          </div>
        ) : (
          <>
            {/* MCP badge */}
            {mcp && !isUser && (
              <div className="flex items-center gap-1.5 mb-2 text-xs text-gray-500">
                <span className="w-1.5 h-1.5 bg-primary-400 rounded-full" />
                {mcp.toUpperCase()}
              </div>
            )}

            {/* Content */}
            <div className={cn(
              'text-sm leading-relaxed whitespace-pre-wrap',
              !isUser && 'text-gray-700'
            )}>
              {content}
            </div>

            {/* Sources */}
            {sources && sources.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-100">
                <div className="text-xs text-gray-500 mb-1.5">Quellen:</div>
                <div className="flex flex-wrap gap-1.5">
                  {sources.map((source, i) => (
                    <span 
                      key={i} 
                      className="px-2 py-0.5 bg-gray-50 text-gray-600 text-xs rounded-md"
                    >
                      {source}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Timestamp */}
      {timestamp && (
        <div className={cn(
          'text-xs text-gray-400 self-end mb-1',
          isUser && 'order-first'
        )}>
          {timestamp.toLocaleTimeString('de-DE', { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </div>
      )}
    </div>
  );
}

// Icons
function UserIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
    </svg>
  );
}

function BotIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
        d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  );
}
