import React from 'react';
import { Brain, Search, FileText, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { Card } from '@/components/ui';

interface ThinkingStep {
    id: string;
    type: 'classify' | 'search' | 'analyze' | 'plan' | 'execute';
    title: string;
    detail?: string;
    status: 'pending' | 'active' | 'done' | 'error';
    timestamp?: string;
}

interface ThinkingPanelProps {
    steps: ThinkingStep[];
    isProcessing: boolean;
    caseData?: any;
    plan?: any;
}

const stepIcons = {
    classify: Brain,
    search: Search,
    analyze: FileText,
    plan: FileText,
    execute: CheckCircle
};

export const ThinkingPanel: React.FC<ThinkingPanelProps> = ({
    steps,
    isProcessing,
    caseData,
    plan
}) => {
    return (
        <div className="h-full flex flex-col bg-muted/20">
            {/* Header */}
            <div className="border-b bg-background p-4">
                <div className="flex items-center gap-2">
                    <Brain className="h-5 w-5 text-primary" />
                    <h2 className="text-lg font-semibold">🧠 عملية التفكير</h2>
                </div>
                <p className="text-sm text-muted-foreground mt-1">
                    متابعة خطوات التحليل والتفكير
                </p>
            </div>

            {/* Thinking Steps */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {steps.length === 0 ? (
                    <div className="text-center text-muted-foreground py-8">
                        <Brain className="h-12 w-12 mx-auto mb-3 opacity-50" />
                        <p>ابدأ محادثة لرؤية عملية التفكير</p>
                    </div>
                ) : (
                    steps.map((step) => {
                        const Icon = stepIcons[step.type] || Brain;
                        return (
                            <Card
                                key={step.id}
                                className={`p-3 transition-all ${step.status === 'active'
                                        ? 'border-primary bg-primary/5 ring-1 ring-primary'
                                        : step.status === 'done'
                                            ? 'border-green-500/50 bg-green-50/50'
                                            : step.status === 'error'
                                                ? 'border-red-500/50 bg-red-50/50'
                                                : 'opacity-60'
                                    }`}
                            >
                                <div className="flex items-start gap-3">
                                    <div className={`p-2 rounded-lg ${step.status === 'active'
                                            ? 'bg-primary/10 text-primary'
                                            : step.status === 'done'
                                                ? 'bg-green-100 text-green-600'
                                                : step.status === 'error'
                                                    ? 'bg-red-100 text-red-600'
                                                    : 'bg-muted text-muted-foreground'
                                        }`}>
                                        {step.status === 'active' ? (
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                        ) : step.status === 'done' ? (
                                            <CheckCircle className="h-4 w-4" />
                                        ) : step.status === 'error' ? (
                                            <AlertCircle className="h-4 w-4" />
                                        ) : (
                                            <Icon className="h-4 w-4" />
                                        )}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="font-medium text-sm">{step.title}</p>
                                        {step.detail && (
                                            <p className="text-xs text-muted-foreground mt-1 truncate">
                                                {step.detail}
                                            </p>
                                        )}
                                        {step.timestamp && (
                                            <p className="text-xs text-muted-foreground mt-1">
                                                {step.timestamp}
                                            </p>
                                        )}
                                    </div>
                                </div>
                            </Card>
                        );
                    })
                )}
            </div>

            {/* Case Summary (if available) */}
            {caseData && (
                <div className="border-t p-4">
                    <h3 className="font-semibold text-sm mb-2">📋 ملخص القضية</h3>
                    <div className="text-xs space-y-1 text-muted-foreground">
                        {caseData.case_id && (
                            <p>رقم: {caseData.case_id.slice(0, 8)}...</p>
                        )}
                        {caseData.status && (
                            <p>الحالة: {caseData.status}</p>
                        )}
                    </div>
                </div>
            )}

            {/* Plan (if available) */}
            {plan?.required_agents && plan.required_agents.length > 0 && (
                <div className="border-t p-4">
                    <h3 className="font-semibold text-sm mb-2">📝 الخطة</h3>
                    <div className="space-y-1">
                        {plan.required_agents.map((agent: any, idx: number) => (
                            <div
                                key={idx}
                                className="text-xs p-2 bg-muted/50 rounded flex items-center gap-2"
                            >
                                <span className="font-mono bg-primary/10 px-1 rounded">
                                    {idx + 1}
                                </span>
                                <span>{agent.type || agent.focus}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Processing Indicator */}
            {isProcessing && (
                <div className="border-t p-4 bg-primary/5">
                    <div className="flex items-center gap-2 text-primary">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span className="text-sm font-medium">جاري المعالجة...</span>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ThinkingPanel;
