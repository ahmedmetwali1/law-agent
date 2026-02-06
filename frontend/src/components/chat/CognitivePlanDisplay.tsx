/**
 * CognitivePlanDisplay Component
 * Shows the execution plan with step-by-step breakdown
 */
import React, { useState } from 'react';
import { ChevronDown, ChevronUp, CheckCircle2, Circle, AlertCircle } from 'lucide-react';

interface PlanStep {
    step_number: number;
    action: string;
    parameters: Record<string, any>;
    reasoning: string;
    is_critical: boolean;
    expected_output?: string;
}

interface ExecutionPlan {
    steps: PlanStep[];
    strategy: string;
    estimated_time?: number;
}

interface CognitivePlanDisplayProps {
    plan: ExecutionPlan;
    executionResults?: Array<{
        step_number: number;
        success: boolean;
    }>;
}

export function CognitivePlanDisplay({ plan, executionResults }: CognitivePlanDisplayProps) {
    const [isExpanded, setIsExpanded] = useState(true);

    const getStepStatus = (stepNumber: number) => {
        if (!executionResults) return 'pending';
        const result = executionResults.find(r => r.step_number === stepNumber);
        if (!result) return 'pending';
        return result.success ? 'success' : 'error';
    };

    const StatusIcon = ({ status }: { status: string }) => {
        if (status === 'success') return <CheckCircle2 className="w-4 h-4 text-green-400" />;
        if (status === 'error') return <AlertCircle className="w-4 h-4 text-red-400" />;
        return <Circle className="w-4 h-4 text-amber-400/50" />;
    };

    return (
        <div className="mb-3 bg-gradient-to-r from-amber-900/20 to-yellow-800/20 border border-amber-600/30 rounded-xl overflow-hidden">
            {/* Header */}
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-amber-900/10 transition-colors"
            >
                <div className="flex items-center gap-2">
                    <span className="text-amber-400 font-semibold text-sm">📋 خطة التنفيذ</span>
                    <span className="text-amber-600/70 text-xs">({plan.steps.length} خطوات)</span>
                </div>
                {isExpanded ? (
                    <ChevronUp className="w-4 h-4 text-amber-400" />
                ) : (
                    <ChevronDown className="w-4 h-4 text-amber-400" />
                )}
            </button>

            {/* Content */}
            {isExpanded && (
                <div className="px-4 pb-4 space-y-3">
                    {/* Strategy */}
                    {plan.strategy && (
                        <div className="text-xs text-amber-300/80 bg-amber-900/20 px-3 py-2 rounded-lg">
                            <span className="font-semibold">الاستراتيجية:</span> {plan.strategy}
                        </div>
                    )}

                    {/* Steps Timeline */}
                    {/* Steps Timeline (Checklist Mode) */}
                    <div className="space-y-3 px-1">
                        {plan.steps.map((step, index) => {
                            const status = getStepStatus(step.step_number);

                            return (
                                <div key={step.step_number} className={`flex items-start gap-3 group transition-all duration-300 ${status === 'success' ? 'opacity-50' : 'opacity-100'}`}>
                                    {/* Checklist Indicator */}
                                    <div className="mt-0.5 shrink-0">
                                        <div className={`
                                            w-5 h-5 rounded-lg border flex items-center justify-center transition-all
                                            ${status === 'success'
                                                ? 'bg-green-500/20 border-green-500/50 text-green-400'
                                                : status === 'error'
                                                    ? 'bg-red-500/20 border-red-500/50 text-red-400'
                                                    : 'bg-black/40 border-amber-600/30 text-amber-600 group-hover:border-amber-500/50'
                                            }
                                        `}>
                                            {status === 'success' ? (
                                                <CheckCircle2 className="w-3.5 h-3.5" />
                                            ) : status === 'error' ? (
                                                <AlertCircle className="w-3.5 h-3.5" />
                                            ) : (
                                                <span className="text-[10px] font-bold">{step.step_number}</span>
                                            )}
                                        </div>
                                    </div>

                                    {/* Step Information */}
                                    <div className="flex-1 min-w-0">
                                        <div className={`
                                            text-xs font-semibold leading-relaxed transition-all
                                            ${status === 'success' ? 'text-gray-500 line-through decoration-gray-600' : 'text-amber-200'}
                                        `}>
                                            {step.reasoning}
                                        </div>
                                        {status !== 'success' && (
                                            <div className="text-[9px] text-amber-600/60 font-mono mt-0.5 flex items-center gap-1">
                                                <span>⚙️ {step.action}</span>
                                                {step.is_critical && <span className="text-red-500/50">[حرج]</span>}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
}
