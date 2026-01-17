import React from 'react';
import { Loader2, CheckCircle, XCircle, Clock } from 'lucide-react';

interface ProgressStep {
    id: string;
    status: 'pending' | 'running' | 'success' | 'error';
    message: string;
    timestamp?: string;
}

interface ToolExecutionProgressProps {
    steps: ProgressStep[];
}

export const ToolExecutionProgress: React.FC<ToolExecutionProgressProps> = ({ steps }) => {
    if (!steps || steps.length === 0) return null;

    return (
        <div className="my-4 space-y-2 bg-muted/30 rounded-lg p-4 border border-border">
            <div className="flex items-center gap-2 mb-3">
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                <span className="font-semibold text-sm" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    جاري التنفيذ...
                </span>
            </div>

            <div className="space-y-2">
                {steps.map((step, index) => (
                    <ProgressStepItem key={step.id || index} step={step} />
                ))}
            </div>
        </div>
    );
};

const ProgressStepItem: React.FC<{ step: ProgressStep }> = ({ step }) => {
    const getIcon = () => {
        switch (step.status) {
            case 'pending':
                return <Clock className="h-4 w-4 text-muted-foreground" />;
            case 'running':
                return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
            case 'success':
                return <CheckCircle className="h-4 w-4 text-green-500" />;
            case 'error':
                return <XCircle className="h-4 w-4 text-red-500" />;
            default:
                return null;
        }
    };

    const getTextColor = () => {
        switch (step.status) {
            case 'running':
                return 'text-blue-600 dark:text-blue-400';
            case 'success':
                return 'text-green-600 dark:text-green-400';
            case 'error':
                return 'text-red-600 dark:text-red-400';
            default:
                return 'text-muted-foreground';
        }
    };

    return (
        <div className={`flex items-center gap-3 p-2 rounded transition-all ${step.status === 'running' ? 'bg-blue-50 dark:bg-blue-950/20' : ''
            }`}>
            {getIcon()}
            <span className={`text-sm flex-1 ${getTextColor()}`} style={{ fontFamily: 'Cairo, sans-serif' }}>
                {step.message}
            </span>
            {step.status === 'running' && (
                <div className="flex gap-1">
                    <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
            )}
        </div>
    );
};

// Tool execution status overlay component
interface ToolExecutionOverlayProps {
    toolName: string;
    status: 'executing' | 'success' | 'error';
    message?: string;
}

export const ToolExecutionOverlay: React.FC<ToolExecutionOverlayProps> = ({
    toolName,
    status,
    message
}) => {
    const getToolDisplayName = (name: string) => {
        const names: Record<string, string> = {
            'create_client': 'إضافة موكل',
            'create_case': 'فتح قضية',
            'create_hearing': 'جدولة جلسة',
            'search_clients': 'البحث عن موكل',
            'search_cases': 'البحث عن قضية',
            'get_today_hearings': 'جلب الجلسات',
            'list_all_clients': 'عرض الموكلين',
            'search_knowledge': 'البحث القانوني'
        };
        return names[name] || name;
    };

    if (status === 'executing') {
        return (
            <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400 py-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm font-medium" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    جاري {getToolDisplayName(toolName)}...
                </span>
            </div>
        );
    }

    if (status === 'success') {
        return (
            <div className="flex items-center gap-2 text-green-600 dark:text-green-400 py-2">
                <CheckCircle className="h-4 w-4" />
                <span className="text-sm font-medium" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    ✅ تم {getToolDisplayName(toolName)} بنجاح!
                </span>
            </div>
        );
    }

    if (status === 'error') {
        return (
            <div className="flex items-center gap-2 text-red-600 dark:text-red-400 py-2">
                <XCircle className="h-4 w-4" />
                <span className="text-sm font-medium" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    ❌ فشل {getToolDisplayName(toolName)}
                </span>
                {message && (
                    <span className="text-xs text-muted-foreground">({message})</span>
                )}
            </div>
        );
    }

    return null;
};
