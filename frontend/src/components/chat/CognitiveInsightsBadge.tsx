/**
 * CognitiveInsightsBadge Component
 * Displays query complexity and intent as a small badge
 */
import React from 'react';
import { Brain, Scale, MessageSquare, HelpCircle } from 'lucide-react';

interface CognitiveDecision {
    complexity: 'simple' | 'moderate' | 'complex' | 'critical';
    intent: 'legal_research' | 'admin_task' | 'chitchat' | 'clarification';
    reasoning: string;
    confidence?: number;
}

interface CognitiveInsightsBadgeProps {
    decision: CognitiveDecision;
}

const complexityLabels = {
    simple: { ar: 'بسيط', color: 'text-green-400' },
    moderate: { ar: 'متوسط', color: 'text-amber-400' },
    complex: { ar: 'معقد', color: 'text-orange-400' },
    critical: { ar: 'حرج', color: 'text-red-400' },
};

const intentIcons = {
    legal_research: { icon: Scale, ar: 'بحث قانوني' },
    admin_task: { icon: Brain, ar: 'مهمة إدارية' },
    chitchat: { icon: MessageSquare, ar: 'محادثة' },
    clarification: { icon: HelpCircle, ar: 'توضيح' },
};

export function CognitiveInsightsBadge({ decision }: CognitiveInsightsBadgeProps) {
    const complexityInfo = complexityLabels[decision.complexity];
    const intentInfo = intentIcons[decision.intent];
    const IntentIcon = intentInfo.icon;

    return (
        <div className="mb-2 group relative">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-amber-900/30 to-yellow-800/30 border border-amber-600/30 rounded-full text-xs">
                {/* Complexity Badge */}
                <span className={`flex items-center gap-1 ${complexityInfo.color} font-semibold`}>
                    <Brain className="w-3 h-3" />
                    {complexityInfo.ar}
                </span>

                {/* Separator */}
                <span className="text-amber-600/50">|</span>

                {/* Intent Badge */}
                <span className="flex items-center gap-1 text-amber-300">
                    <IntentIcon className="w-3 h-3" />
                    {intentInfo.ar}
                </span>

                {/* Confidence (if available) */}
                {decision.confidence && (
                    <>
                        <span className="text-amber-600/50">|</span>
                        <span className="text-amber-400/70 text-[10px]">
                            {Math.round(decision.confidence * 100)}%
                        </span>
                    </>
                )}
            </div>

            {/* Tooltip with reasoning */}
            <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block z-10 animate-fade-in">
                <div className="bg-gray-900 border border-amber-600/50 rounded-lg px-3 py-2 text-xs text-amber-100 max-w-xs shadow-xl">
                    <div className="font-semibold text-amber-400 mb-1">التحليل الداخلي:</div>
                    <div className="text-gray-300">{decision.reasoning}</div>
                    {/* Arrow */}
                    <div className="absolute top-full left-4 -mt-1">
                        <div className="border-4 border-transparent border-t-amber-600/50"></div>
                    </div>
                </div>
            </div>
        </div>
    );
}
