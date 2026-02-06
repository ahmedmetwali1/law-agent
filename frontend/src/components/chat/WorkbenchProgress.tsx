import React, { useState } from 'react';
import { CheckCircle2, Circle, AlertCircle, Loader2, Brain, PlayCircle, HardDrive, ChevronRight, ChevronDown } from 'lucide-react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export interface ProgressItem {
    id: string;
    label: string;
    status: 'pending' | 'running' | 'done' | 'error';
    type: 'thought' | 'action' | 'analysis' | 'planning';
    details?: string;
    duration?: string;
}

interface WorkbenchProgressProps {
    items: ProgressItem[];
}

export const WorkbenchProgress: React.FC<WorkbenchProgressProps> = ({ items }) => {
    // Tracking expanded state per item label/id
    const [expandedItems, setExpandedItems] = useState<Record<string, boolean>>({});

    const toggleExpand = (id: string) => {
        setExpandedItems(prev => ({
            ...prev,
            [id]: !prev[id]
        }));
    };

    return (
        <div className="flex flex-col gap-0.5 w-full font-sans py-2 ml-11">
            {items.map((item, idx) => {
                const isLast = idx === items.length - 1;
                const isRunning = item.status === 'running';
                const isExpanded = !!expandedItems[item.id];
                const hasDetails = !!item.details;

                return (
                    <div key={item.id} className="relative flex gap-4 group">
                        {/* Vertical Timeline Line */}
                        {!isLast && (
                            <div className="absolute left-[9px] top-5 bottom-0 w-[1px] bg-white/5 group-hover:bg-gold-500/10 transition-colors" />
                        )}

                        {/* Status Icon */}
                        <div className="mt-1.5 shrink-0 z-10">
                            {item.status === 'done' ? (
                                <div className="p-0.5 bg-green-500/10 rounded-full border border-green-500/20">
                                    <CheckCircle2 className="w-3.5 h-3.5 text-green-400/80" />
                                </div>
                            ) : item.status === 'error' ? (
                                <AlertCircle className="w-3.5 h-3.5 text-red-500" />
                            ) : item.status === 'running' ? (
                                <Loader2 className="w-3.5 h-3.5 text-gold-500 animate-spin" />
                            ) : (
                                <Circle className="w-3.5 h-3.5 text-white/20" />
                            )}
                        </div>

                        {/* Content */}
                        <div className="flex flex-col flex-1 pb-4">
                            <div
                                onClick={() => hasDetails && toggleExpand(item.id)}
                                className={`
                                    text-[11px] font-medium tracking-tight transition-colors flex items-center gap-2
                                    ${isRunning ? 'text-gold-500' : item.status === 'done' ? 'text-gray-400' : 'text-gray-500'}
                                    ${hasDetails ? 'cursor-pointer hover:text-white/80' : ''}
                                `}
                            >
                                {item.type === 'thought' && <Brain className="w-3 h-3 opacity-50" />}
                                {item.type === 'action' && <HardDrive className="w-3 h-3 opacity-50" />}
                                {item.type === 'planning' && <PlayCircle className="w-3 h-3 opacity-50" />}

                                <span className={`${isRunning ? 'animate-pulse' : ''}`}>{item.label}</span>

                                {hasDetails && (
                                    <span className="ml-1 opacity-40">
                                        {isExpanded ? <ChevronDown className="w-2.5 h-2.5" /> : <ChevronRight className="w-2.5 h-2.5" />}
                                    </span>
                                )}

                                {item.duration && <span className="text-[9px] opacity-30 font-mono ml-auto">{item.duration}</span>}
                            </div>

                            {hasDetails && isExpanded && (
                                <div className="mt-1.5 p-2 bg-obsidian-900/40 rounded-lg border border-white/5 text-[10px] text-gray-400 leading-relaxed shadow-sm animate-in fade-in slide-in-from-top-1 duration-200">
                                    <Markdown remarkPlugins={[remarkGfm]}>{item.details}</Markdown>
                                </div>
                            )}
                        </div>
                    </div>
                );
            })}
        </div>
    );
};
