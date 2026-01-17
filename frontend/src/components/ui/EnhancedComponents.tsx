import React from 'react';
import { Loader2, Sparkles, Check } from 'lucide-react';

export type ThinkingStatus = 'pending' | 'active' | 'completed' | 'error';

interface ThinkingStep {
    id: string;
    label: string;
    status: ThinkingStatus;
    duration?: number;
}

interface LiveThinkingStreamProps {
    steps: ThinkingStep[];
    currentStep?: string;
}

export const LiveThinkingStream: React.FC<LiveThinkingStreamProps> = ({
    steps,
    currentStep
}) => {
    return (
        <div className="space-y-2 p-4 bg-muted/30 rounded-lg border border-border animate-fade-in">
            <div className="flex items-center gap-2 mb-3">
                <Sparkles className="h-4 w-4 text-primary animate-pulse-soft" />
                <span className="text-sm font-semibold text-primary">جاري التفكير...</span>
            </div>

            {steps.map((step, index) => (
                <ThinkingStepItem
                    key={step.id}
                    step={step}
                    isLast={index === steps.length - 1}
                />
            ))}
        </div>
    );
};

interface ThinkingStepItemProps {
    step: ThinkingStep;
    isLast: boolean;
}

const ThinkingStepItem: React.FC<ThinkingStepItemProps> = ({ step, isLast }) => {
    const getStatusColor = () => {
        switch (step.status) {
            case 'completed': return 'text-success border-success/30 bg-success/5';
            case 'active': return 'text-primary border-primary/30 bg-primary/5 animate-pulse-soft';
            case 'error': return 'text-error border-error/30 bg-error/5';
            default: return 'text-muted-foreground border-border bg-transparent';
        }
    };

    const getIcon = () => {
        switch (step.status) {
            case 'completed':
                return <Check className="h-4 w-4" />;
            case 'active':
                return <Loader2 className="h-4 w-4 animate-spin" />;
            case 'error':
                return <span className="text-xs">✗</span>;
            default:
                return <div className="h-2 w-2 rounded-full bg-muted-foreground/30" />;
        }
    };

    return (
        <div className={`
            flex items-center gap-3 p-2.5 rounded-lg border transition-all duration-300
            ${getStatusColor()}
        `}>
            <div className="flex items-center justify-center w-6 h-6">
                {getIcon()}
            </div>

            <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{step.label}</p>
                {step.duration && step.status === 'completed' && (
                    <p className="text-xs opacity-70">{step.duration.toFixed(1)}s</p>
                )}
            </div>

            {step.status === 'active' && (
                <div className="flex gap-1">
                    <div className="w-1 h-1 rounded-full bg-current animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-1 h-1 rounded-full bg-current animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-1 h-1 rounded-full bg-current animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
            )}
        </div>
    );
};

// Confidence Meter Component
interface ConfidenceMeterProps {
    confidence: number; // 0-100
    label?: string;
}

export const ConfidenceMeter: React.FC<ConfidenceMeterProps> = ({
    confidence,
    label = 'مستوى الثقة'
}) => {
    const getColor = () => {
        if (confidence >= 80) return 'success';
        if (confidence >= 60) return 'primary';
        if (confidence >= 40) return 'warning';
        return 'error';
    };

    const color = getColor();

    return (
        <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
                <span className="font-medium">{label}</span>
                <span className={`font-bold text-${color}`}>{confidence}%</span>
            </div>

            <div className="relative h-2 bg-muted rounded-full overflow-hidden">
                <div
                    className={`
                        absolute inset-y-0 right-0 rounded-full transition-all duration-700 ease-out
                        ${color === 'success' ? 'bg-gradient-to-l from-success to-success-light' :
                            color === 'primary' ? 'bg-gradient-to-l from-primary to-primary-light' :
                                color === 'warning' ? 'bg-gradient-to-l from-warning to-warning-light' :
                                    'bg-gradient-to-l from-error to-error-light'}
                    `}
                    style={{ width: `${confidence}%` }}
                />
            </div>
        </div>
    );
};

// Typing Indicator
export const TypingIndicator: React.FC = () => {
    return (
        <div
            className="flex items-center gap-2 px-4 py-3 rounded-lg border border-border w-fit animate-fade-in"
            style={{ backgroundColor: 'hsl(var(--surface))' }}
        >
            <div className="flex gap-1">
                <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
            <span className="text-sm text-muted-foreground">المحامي يكتب...</span>
        </div>
    );
};

// Ripple Button
interface RippleButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'ghost';
    children: React.ReactNode;
}

export const RippleButton: React.FC<RippleButtonProps> = ({
    variant = 'primary',
    children,
    className = '',
    ...props
}) => {
    const [ripples, setRipples] = React.useState<Array<{ x: number; y: number; id: number }>>([]);

    const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const newRipple = { x, y, id: Date.now() };
        setRipples(prev => [...prev, newRipple]);

        setTimeout(() => {
            setRipples(prev => prev.filter(r => r.id !== newRipple.id));
        }, 600);

        props.onClick?.(e);
    };

    const variantClasses = {
        primary: 'bg-primary text-primary-foreground hover:bg-primary-dark',
        secondary: 'text-foreground border border-border',
        ghost: 'bg-transparent text-foreground hover:bg-muted'
    };

    const variantStyles = {
        primary: {},
        secondary: { backgroundColor: 'hsl(var(--surface))' },
        ghost: {}
    };

    return (
        <button
            {...props}
            onClick={handleClick}
            style={variantStyles[variant]}
            className={`
                relative overflow-hidden px-4 py-2 rounded-lg font-medium
                transition-all duration-200 active:scale-95
                ${variantClasses[variant]}
                ${className}
            `}
        >
            {ripples.map(ripple => (
                <span
                    key={ripple.id}
                    className="absolute bg-white/30 rounded-full animate-ripple"
                    style={{
                        left: ripple.x,
                        top: ripple.y,
                        width: '100px',
                        height: '100px',
                        transform: 'translate(-50%, -50%)'
                    }}
                />
            ))}
            {children}
        </button>
    );
};
