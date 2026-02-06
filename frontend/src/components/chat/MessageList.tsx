import React, { useRef, useEffect } from 'react';
import { ChatBubble } from './ChatBubble';
import { ToolAccordion } from './ToolAccordion';
import { PulsingLoader } from './PulsingLoader';
import { ChatEmptyState } from './ChatEmptyState';
import { ToolExecutionProgress } from './ToolExecutionProgress';
import { ExecutionLog } from '../../hooks/useRealtimeStatus';

interface MessageListProps {
    messages: any[];
    isThinking: boolean;
    realtimeStatus?: string | null;
    executionLogs?: ExecutionLog[];
    onSuggestionClick?: (text: string) => void;
}

export const MessageList: React.FC<MessageListProps> = ({ messages, isThinking, realtimeStatus, executionLogs, onSuggestionClick }) => {
    const bottomRef = useRef<HTMLDivElement>(null);

    // Auto-scroll logic
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isThinking, executionLogs]);

    return (
        <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-gray-700 hover:scrollbar-thumb-gold-500/50">
            {messages.length === 0 && (
                <div className="h-full flex flex-col justify-center">
                    <ChatEmptyState onSuggestionClick={onSuggestionClick || (() => { })} />
                </div>
            )}

            {messages.map((msg, idx) => {
                if (msg.role === 'tool') {
                    // Extract tool name if available in metadata, fallback to generic
                    const toolName = msg.metadata?.tool_name || msg.name || 'System Tool';
                    return <ToolAccordion key={`tool-${idx}`} content={msg.content} toolName={toolName} />;
                }

                return (
                    <ChatBubble
                        key={msg.id || idx}
                        role={msg.role}
                        content={msg.content}
                        createdAt={msg.created_at}
                        metadata={msg.metadata}
                    />
                );
            })}

            {isThinking && (
                <div className="w-full flex flex-col items-center py-4 gap-4">
                    {/* ✅ Show Step-by-Step Progress */}
                    {executionLogs && executionLogs.length > 0 && (
                        <div className="w-full max-w-2xl animate-fade-in-up">
                            <ToolExecutionProgress steps={executionLogs} />
                        </div>
                    )}

                    {/* Show Simple Pulse if no logs or as complement */}
                    <PulsingLoader realtimeStatus={realtimeStatus} />
                </div>
            )}

            <div ref={bottomRef} className="h-1" />
        </div>
    );
};
