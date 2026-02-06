import React from 'react';
import {
    CheckCircle2,
    Circle,
    AlertCircle,
    Loader2,
    Brain,
    Zap,
    MinusCircle,
    GitBranch,
    ChevronDown,
    Sparkles
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../../lib/utils'; // Relative path to ensure resolution

export interface ExecutionStep {
    step_id: number;
    title: string;
    status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';
    action: string;
    start_time?: string;
    end_time?: string;
    duration?: number;
    dependencies: number[];
    reasoning?: string;
    output_preview?: string;
}

interface ExecutionPlan {
    strategy: string;
    steps: ExecutionStep[];
}

interface ExecutionTimelineProps {
    plan: ExecutionPlan;
}

export function ExecutionTimeline({ plan }: ExecutionTimelineProps) {
    if (!plan || !plan.steps) return null;

    const completedCount = plan.steps.filter(s => s.status === 'completed').length;
    const progress = (completedCount / plan.steps.length) * 100;

    return (
        <div className="space-y-4 p-4 bg-slate-950/40 backdrop-blur-md rounded-xl border border-slate-800/50 shadow-2xl">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="p-1.5 bg-purple-500/20 rounded-lg">
                        <Brain className="w-4 h-4 text-purple-400" />
                    </div>
                    <h3 className="text-sm font-bold text-slate-200 tracking-tight">
                        خطة التنفيذ الذكية
                    </h3>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">Progress</span>
                    <div className="px-2 py-0.5 bg-slate-900 rounded-full border border-slate-800 text-[10px] font-bold text-slate-300">
                        {completedCount}/{plan.steps.length}
                    </div>
                </div>
            </div>

            {/* Strategy Monologue */}
            {plan.strategy && (
                <div className="relative overflow-hidden p-3 bg-slate-900/40 rounded-lg border-r-2 border-purple-500/50">
                    <div className="absolute top-0 right-0 p-1 opacity-10">
                        <Sparkles className="w-8 h-8 text-purple-400" />
                    </div>
                    <p className="text-[11px] text-slate-400 leading-relaxed italic pr-1">
                        "{plan.strategy}"
                    </p>
                </div>
            )}

            {/* Steps List */}
            <div className="space-y-3 relative">
                {plan.steps.map((step, idx) => (
                    <StepCard
                        key={step.step_id}
                        step={step}
                        isActive={step.status === 'in_progress'}
                        isNext={idx > 0 && plan.steps[idx - 1].status === 'completed' && step.status === 'pending'}
                    />
                ))}
            </div>

            {/* Visual Progress Bar */}
            <div className="space-y-1.5 pt-2">
                <div className="flex justify-between text-[9px] text-slate-500 font-mono uppercase tracking-tighter">
                    <span>Operational Integrity</span>
                    <span>{Math.round(progress)}%</span>
                </div>
                <div className="relative h-1 bg-slate-800 rounded-full overflow-hidden">
                    <motion.div
                        className="absolute top-0 right-0 h-full bg-gradient-to-l from-purple-500 via-blue-500 to-emerald-500"
                        initial={{ width: 0 }}
                        animate={{ width: `${progress}%` }}
                        transition={{ duration: 0.8, ease: "circOut" }}
                    />
                </div>
            </div>
        </div>
    );
}

interface StepCardProps {
    step: ExecutionStep;
    isActive: boolean;
    isNext: boolean;
}

function StepCard({ step, isActive, isNext }: StepCardProps) {
    const statusConfig = {
        pending: {
            icon: Circle,
            color: 'text-slate-600',
            bg: 'bg-slate-900/20',
            border: 'border-slate-800/30'
        },
        in_progress: {
            icon: Loader2,
            color: 'text-amber-400',
            bg: 'bg-amber-950/10',
            border: 'border-amber-700/30',
            pulse: true
        },
        completed: {
            icon: CheckCircle2,
            color: 'text-emerald-400',
            bg: 'bg-emerald-950/10',
            border: 'border-emerald-700/30'
        },
        failed: {
            icon: AlertCircle,
            color: 'text-rose-400',
            bg: 'bg-rose-950/10',
            border: 'border-rose-700/30'
        },
        skipped: {
            icon: MinusCircle,
            color: 'text-slate-500',
            bg: 'bg-slate-900/10',
            border: 'border-slate-800/20'
        }
    };

    const config = statusConfig[step.status] || statusConfig.pending;
    const Icon = config.icon;

    return (
        <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className={cn(
                "relative p-3 rounded-xl border transition-all duration-500",
                config.bg,
                config.border,
                isActive && "ring-1 ring-amber-500/30 shadow-lg shadow-amber-500/5",
                isNext && "border-blue-500/20"
            )}
        >
            <div className="flex items-start gap-3">
                {/* Status Icon Wrapper */}
                <div className={cn("mt-0.5 relative", ('pulse' in config && config.pulse) && "animate-pulse")}>
                    {isActive ? (
                        <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ repeat: Infinity, duration: 3, ease: "linear" }}
                        >
                            <Icon className={cn("w-4 h-4", config.color)} />
                        </motion.div>
                    ) : (
                        <Icon className={cn("w-4 h-4", config.color)} />
                    )}

                    {isActive && (
                        <motion.div
                            className="absolute inset-0 rounded-full bg-amber-500/20"
                            animate={{ scale: [1, 1.8, 1], opacity: [0.3, 0, 0.3] }}
                            transition={{ duration: 2, repeat: Infinity }}
                        />
                    )}
                </div>

                <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                        <h4 className={cn(
                            "text-xs font-semibold truncate transition-colors",
                            isActive ? "text-amber-200" : "text-slate-200",
                            step.status === 'skipped' && "text-slate-500 line-through"
                        )}>
                            {step.title}
                        </h4>
                        {step.duration && step.status === 'completed' && (
                            <span className="text-[9px] font-mono text-slate-500">
                                {step.duration.toFixed(1)}s
                            </span>
                        )}
                    </div>

                    <AnimatePresence>
                        {isActive && step.reasoning && (
                            <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: 'auto', opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                className="overflow-hidden"
                            >
                                <p className="text-[10px] text-slate-400 mt-1.5 leading-relaxed pr-0 border-r border-amber-500/20 pr-2">
                                    <span className="text-amber-500/50">💭</span> {step.reasoning}
                                </p>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Action & Deps Badge */}
                    <div className="flex items-center gap-2 mt-2.5">
                        <div className="inline-flex items-center px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-[9px] font-mono text-slate-400">
                            <Zap className="w-2.5 h-2.5 mr-1 text-blue-400/70" />
                            {step.action}
                        </div>
                        {step.dependencies.length > 0 && (
                            <div className="inline-flex items-center px-1.5 py-0.5 rounded bg-slate-900/50 border border-slate-800/50 text-[9px] text-slate-500">
                                <GitBranch className="w-2.5 h-2.5 mr-1" />
                                {step.dependencies.length} deps
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
