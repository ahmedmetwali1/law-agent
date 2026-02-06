import React from 'react';
import { CheckCircle2, Circle, Clock, Loader2, PlayCircle } from 'lucide-react';

export interface WorkflowStep {
    step: string;
    label: string; // e.g., "استخلاص الوقائع"
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
    description?: string;
}

interface WorkflowProgressProps {
    plan: WorkflowStep[];
}

export const WorkflowProgress: React.FC<WorkflowProgressProps> = ({ plan }) => {
    if (!plan || plan.length === 0) return null;

    return (
        <div className="w-full my-4 bg-white/5 border border-white/10 rounded-xl p-4 animate-fade-in">
            <h4 className="text-xs font-semibold text-gray-400 mb-4 flex items-center gap-2">
                <PlayCircle className="w-4 h-4 text-primary" />
                خطة العمل التنفيذية
            </h4>

            <div className="relative">
                {/* Vertical Line */}
                <div className="absolute top-2 bottom-2 right-[19px] w-0.5 bg-gray-700/50" />

                <div className="space-y-4 relative z-10">
                    {plan.map((step, index) => {
                        const isCompleted = step.status === 'completed';
                        const isInProgress = step.status === 'in_progress';
                        const isPending = step.status === 'pending';

                        return (
                            <div key={step.step || index} className="flex items-start gap-4 mr-1">
                                {/* Icon */}
                                <div className={`
                                    w-9 h-9 rounded-full flex items-center justify-center shrink-0 border-2 transition-all duration-300
                                    ${isCompleted ? 'bg-green-500/10 border-green-500 text-green-500' : ''}
                                    ${isInProgress ? 'bg-blue-500/10 border-blue-500 text-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.5)]' : ''}
                                    ${isPending ? 'bg-gray-800 border-gray-700 text-gray-500' : ''}
                                `}>
                                    {isCompleted && <CheckCircle2 className="w-5 h-5" />}
                                    {isInProgress && <Loader2 className="w-5 h-5 animate-spin" />}
                                    {isPending && <Circle className="w-5 h-5" />}
                                </div>

                                {/* Content */}
                                <div className="pt-1 flex-1">
                                    <div className="flex items-center justify-between">
                                        <h5 className={`font-medium ${isPending ? 'text-gray-500' : 'text-gray-200'}`}>
                                            {step.label}
                                        </h5>
                                        {isInProgress && (
                                            <span className="text-[10px] bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded-full animate-pulse">
                                                جاري العمل...
                                            </span>
                                        )}
                                    </div>
                                    {step.description && (
                                        <p className="text-xs text-gray-500 mt-1">{step.description}</p>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};
