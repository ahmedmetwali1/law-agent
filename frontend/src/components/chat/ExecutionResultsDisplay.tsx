/**
 * ExecutionResultsDisplay Component
 * Shows results from each executed step
 */
import React, { useState } from 'react';
import { ChevronDown, ChevronUp, CheckCircle2, XCircle, Clock } from 'lucide-react';

interface ExecutionResult {
    step_number: number;
    action: string;
    success: boolean;
    output?: any;
    error_message?: string;
    execution_time?: number;
}

interface ExecutionResultsDisplayProps {
    results: ExecutionResult[];
}

export function ExecutionResultsDisplay({ results }: ExecutionResultsDisplayProps) {
    const [isExpanded, setIsExpanded] = useState(true);
    const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());

    const toggleStepExpansion = (stepNumber: number) => {
        setExpandedSteps(prev => {
            const newSet = new Set(prev);
            if (newSet.has(stepNumber)) {
                newSet.delete(stepNumber);
            } else {
                newSet.add(stepNumber);
            }
            return newSet;
        });
    };

    const successCount = results.filter(r => r.success).length;
    const failureCount = results.length - successCount;

    return (
        <div className="mb-3 bg-gradient-to-r from-emerald-900/20 to-teal-800/20 border border-emerald-600/30 rounded-xl overflow-hidden">
            {/* Header */}
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-emerald-900/10 transition-colors"
            >
                <div className="flex items-center gap-2">
                    <span className="text-emerald-400 font-semibold text-sm">✅ نتائج التنفيذ</span>
                    <div className="flex items-center gap-2 text-xs">
                        <span className="text-green-400">{successCount} نجحت</span>
                        {failureCount > 0 && (
                            <>
                                <span className="text-emerald-600/50">·</span>
                                <span className="text-red-400">{failureCount} فشلت</span>
                            </>
                        )}
                    </div>
                </div>
                {isExpanded ? (
                    <ChevronUp className="w-4 h-4 text-emerald-400" />
                ) : (
                    <ChevronDown className="w-4 h-4 text-emerald-400" />
                )}
            </button>

            {/* Content */}
            {isExpanded && (
                <div className="px-4 pb-4 space-y-2">
                    {results.map((result) => {
                        const isStepExpanded = expandedSteps.has(result.step_number);

                        return (
                            <div
                                key={result.step_number}
                                className={`rounded-lg border ${result.success
                                        ? 'bg-green-900/10 border-green-600/30'
                                        : 'bg-red-900/10 border-red-600/30'
                                    }`}
                            >
                                {/* Result Header */}
                                <button
                                    onClick={() => toggleStepExpansion(result.step_number)}
                                    className="w-full px-3 py-2 flex items-center justify-between hover:bg-black/10 transition-colors"
                                >
                                    <div className="flex items-center gap-2">
                                        {result.success ? (
                                            <CheckCircle2 className="w-4 h-4 text-green-400" />
                                        ) : (
                                            <XCircle className="w-4 h-4 text-red-400" />
                                        )}
                                        <span className="text-sm font-semibold text-gray-200">
                                            {result.step_number}. {result.action}
                                        </span>
                                        {result.execution_time && (
                                            <span className="flex items-center gap-1 text-[10px] text-gray-500">
                                                <Clock className="w-3 h-3" />
                                                {result.execution_time.toFixed(2)}s
                                            </span>
                                        )}
                                    </div>
                                    {(result.output || result.error_message) && (
                                        isStepExpanded ? (
                                            <ChevronUp className="w-3 h-3 text-gray-400" />
                                        ) : (
                                            <ChevronDown className="w-3 h-3 text-gray-400" />
                                        )
                                    )}
                                </button>

                                {/* Expanded Output */}
                                {isStepExpanded && (result.output || result.error_message) && (
                                    <div className="px-3 pb-3 pt-1">
                                        <div className={`text-xs rounded-lg p-2 ${result.success
                                                ? 'bg-green-950/30 text-green-300'
                                                : 'bg-red-950/30 text-red-300'
                                            } font-mono overflow-x-auto`}>
                                            <pre className="whitespace-pre-wrap">
                                                {result.error_message || JSON.stringify(result.output, null, 2)}
                                            </pre>
                                        </div>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
