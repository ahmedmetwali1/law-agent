
import React from 'react';
import { Calendar } from 'lucide-react';

export interface TimelineEvent {
    date: string;
    title: string;
    description?: string;
    status?: 'completed' | 'pending' | 'future';
}

interface TimelineProps {
    data: {
        title?: string;
        events: TimelineEvent[];
    }
}

export const Timeline: React.FC<TimelineProps> = ({ data }) => {
    return (
        <div className="my-4 rounded-xl border border-[#3d4450] bg-[#252a30] p-4">
            {data.title && (
                <div className="mb-4 flex items-center gap-2 border-b border-[#3d4450] pb-2">
                    <Calendar className="h-5 w-5 text-[#2a8f7a]" />
                    <h3 className="font-semibold text-white">{data.title}</h3>
                </div>
            )}

            <div className="relative space-y-4 pl-4 before:absolute before:right-auto before:left-[11px] before:top-2 before:h-[calc(100%-16px)] before:w-[2px] before:bg-[#3d4450]">
                {data.events.map((event, idx) => (
                    <div key={idx} className="relative pl-6">
                        {/* Dot */}
                        <div className={`absolute left-0 top-1.5 h-6 w-6 rounded-full border-4 border-[#252a30] ${event.status === 'completed' ? 'bg-green-500' :
                                event.status === 'pending' ? 'bg-yellow-500' : 'bg-gray-500'
                            }`} />

                        <div className="rounded-lg bg-[#2d3136] p-3 transition-colors hover:bg-[#32383d]">
                            <div className="flex flex-col sm:flex-row sm:justify-between">
                                <h4 className="font-medium text-white">{event.title}</h4>
                                <span className="text-xs font-mono text-gray-400 sm:text-right">{event.date}</span>
                            </div>
                            {event.description && (
                                <p className="mt-1 text-sm text-gray-400">{event.description}</p>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};
