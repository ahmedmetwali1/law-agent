import React, { useEffect, useState, useRef } from 'react';
import { useCaseStore } from '@/store';
import { Card } from '@/components/ui';
import {
    Brain,
    CheckCircle2,
    Circle,
    Loader2,
    Clock,
    AlertCircle,
    ChevronRight,
    Play,
    Activity
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Basic ScrollArea component to resolve missing import if UI lib is incomplete
const ScrollArea = React.forwardRef<HTMLDivElement, { className?: string; children: React.ReactNode }>(
    ({ className, children }, ref) => (
        <div ref={ref} className={`overflow-auto ${className || ''}`}>
            {children}
        </div>
    )
);

// Types from our backend events
interface PlanStep {
    step_id: string;
    description: string;
    step_type?: string;
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
    result?: string;
    message?: string;
}

interface PlanState {
    plan_id: string;
    goal: string;
    steps: PlanStep[];
    status: 'planning' | 'executing' | 'completed' | 'failed';
    current_step_index: number;
}

export const PlanViewer: React.FC = () => {
    const { currentCase, isProcessing } = useCaseStore();
    const [plan, setPlan] = useState<PlanState | null>(null);
    const [logs, setLogs] = useState<string[]>([]);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll logs
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    useEffect(() => {
        if (!currentCase?.case_id || !isProcessing) return;

        // Connect to SSE stream using relative path (via Vite proxy)
        console.log(`🔗 Connecting to stream for case: ${currentCase.case_id}`);
        // Use relative path to leverage Vite proxy
        const eventSource = new EventSource(`/api/cases/${currentCase.case_id}/stream`);

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('📡 Event:', data);

                if (data.type === 'PLAN_CREATED') {
                    setPlan({
                        plan_id: data.data.plan_id,
                        goal: data.data.goal,
                        steps: data.data.steps.map((s: any) => ({
                            ...s,
                            status: 'pending'
                        })),
                        status: 'executing',
                        current_step_index: 0
                    });
                    setLogs(prev => [...prev, `📋 Plan created: ${data.data.goal}`]);
                }

                else if (data.type === 'STEP_START') {
                    setPlan(prev => {
                        if (!prev) return null;
                        return {
                            ...prev,
                            current_step_index: prev.steps.findIndex(s => s.step_id === data.data.step_id),
                            steps: prev.steps.map(s =>
                                s.step_id === data.data.step_id
                                    ? { ...s, status: 'in_progress' }
                                    : s
                            )
                        };
                    });
                    setLogs(prev => [...prev, `▶️ Starting step: ${data.data.step_id}`]);
                }

                else if (data.type === 'STEP_COMPLETE') {
                    setPlan(prev => {
                        if (!prev) return null;
                        return {
                            ...prev,
                            steps: prev.steps.map(s =>
                                s.step_id === data.data.step_id
                                    ? { ...s, status: 'completed', result: data.data.result, message: data.data.message }
                                    : s
                            )
                        };
                    });
                    setLogs(prev => [...prev, `✅ Completed step: ${data.data.message || data.data.step_id}`]);
                }

                else if (data.type === 'PLAN_COMPLETED') {
                    setPlan(prev => prev ? { ...prev, status: 'completed' } : null);
                    setLogs(prev => [...prev, `🎉 Plan execution completed!`]);
                    eventSource.close();
                }

                else if (data.type === 'ERROR') {
                    setLogs(prev => [...prev, `❌ Error: ${data.data.message}`]);
                    eventSource.close();
                }

            } catch (err) {
                console.error('Error parsing SSE:', err);
            }
        };

        eventSource.onerror = (err) => {
            console.error('SSE Error:', err);
            eventSource.close();
        };

        return () => {
            eventSource.close();
        };
    }, [currentCase?.case_id, isProcessing]);

    if (!isProcessing && !plan) {
        return (
            <div className="flex flex-col items-center justify-center p-12 text-muted-foreground h-64 border-2 border-dashed border-primary/20 rounded-xl bg-muted/5 backdrop-blur-sm">
                <Brain className="h-16 w-16 mb-4 text-primary/30 animate-pulse" />
                <p className="text-lg font-medium">بانتظار بدء التحليل الذكي...</p>
                <p className="text-sm opacity-70">سيظهر مسار التفكير هنا تلقائياً</p>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full space-y-4" dir="rtl">
            {/* Header */}
            <div className="flex items-center justify-between p-4 bg-gradient-to-l from-primary/10 to-transparent rounded-xl border border-primary/10 shadow-sm backdrop-blur-md">
                <div className="flex items-center gap-3">
                    <div className="p-3 bg-primary/20 rounded-full shadow-inner ring-1 ring-primary/30 animate-pulse">
                        <Brain className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                        <h3 className="font-bold text-base text-foreground">عملية التفكير النشط</h3>
                        <p className="text-xs text-muted-foreground font-mono mt-0.5">{plan?.goal || 'جاري تحليل القضية...'}</p>
                    </div>
                </div>
                <div className={`text-xs font-bold px-3 py-1.5 rounded-full border shadow-sm transition-colors ${plan?.status === 'completed' ? 'bg-green-500/10 text-green-600 border-green-200' :
                        plan?.status === 'executing' ? 'bg-blue-500/10 text-blue-600 border-blue-200 animate-pulse' :
                            'bg-muted text-muted-foreground border-border'
                    }`}>
                    {plan?.status === 'completed' ? 'مكتمل ✅' :
                        plan?.status === 'executing' ? 'جاري التنفيذ ⚡' :
                            'قيد الانتظار ⏳'}
                </div>
            </div>

            {/* Steps Timeline & Terminal */}
            <div className="flex-1 overflow-hidden flex flex-col lg:flex-row gap-4 h-[500px]">
                {/* Steps List */}
                <Card className="flex-1 overflow-hidden flex flex-col bg-surface/50 backdrop-blur-sm border-border/50 shadow-lg hover:shadow-xl transition-shadow duration-300">
                    <div className="p-4 border-b bg-muted/30 flex items-center gap-2">
                        <Play className="h-4 w-4 text-primary" />
                        <h4 className="font-bold text-sm">خطوات التنفيذ</h4>
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-primary/20 hover:scrollbar-thumb-primary/40 scrollbar-track-transparent">
                        <AnimatePresence>
                            {plan?.steps.map((step, idx) => (
                                <motion.div
                                    key={step.step_id}
                                    initial={{ opacity: 0, x: 20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: idx * 0.1 }}
                                    className={`relative pr-8 pl-4 pb-6 border-r-2 last:border-0 last:pb-0 group ${step.status === 'completed' ? 'border-green-500/30' :
                                            step.status === 'in_progress' ? 'border-primary/50' : 'border-muted'
                                        }`}
                                >
                                    {/* Timeline Node */}
                                    <div className={`absolute -right-[9px] top-0 h-4 w-4 rounded-full border-2 bg-background z-10 flex items-center justify-center transition-all duration-300 ${step.status === 'completed' ? 'border-green-500 text-green-500 scale-110' :
                                            step.status === 'in_progress' ? 'border-primary animate-pulse scale-125 shadow-[0_0_10px_rgba(var(--primary),0.5)]' :
                                                'border-muted text-muted-foreground'
                                        }`}>
                                        {step.status === 'completed' ? <CheckCircle2 className="h-3 w-3" /> :
                                            step.status === 'in_progress' ? <div className="h-2 w-2 bg-primary rounded-full" /> :
                                                <Circle className="h-2 w-2" />}
                                    </div>

                                    {/* Card Content */}
                                    <div className={`p-4 rounded-xl border transition-all duration-300 ${step.status === 'in_progress' ? 'bg-primary/5 border-primary/30 shadow-md translate-x-[-4px]' :
                                            step.status === 'completed' ? 'bg-gradient-to-br from-green-50/50 to-transparent border-green-200/50' :
                                                'bg-card/50 border-border/40 hover:bg-card hover:border-border/80'
                                        }`}>
                                        <div className="flex justify-between items-start gap-4">
                                            <p className="text-sm font-semibold leading-relaxed">{step.description}</p>
                                            {step.status === 'in_progress' && <Loader2 className="h-4 w-4 animate-spin text-primary flex-shrink-0" />}
                                        </div>
                                        {step.message && (
                                            <div className="mt-3 text-xs bg-background/80 p-2.5 rounded-lg border border-border/50 text-muted-foreground leading-relaxed flex items-start gap-2">
                                                <ChevronRight className="h-3 w-3 mt-0.5 text-primary/50" />
                                                {step.message}
                                            </div>
                                        )}
                                    </div>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    </div>
                </Card>

                {/* Logs Terminal */}
                <Card className="lg:w-[350px] bg-[#0c0c0c] text-green-500 font-mono text-xs p-0 overflow-hidden flex flex-col shadow-2xl border-gray-800 rounded-xl ring-1 ring-white/10">
                    <div className="flex items-center justify-between px-4 py-2 border-b border-gray-800 bg-[#1a1a1a]">
                        <span className="flex items-center gap-2 opacity-70">
                            <Activity className="h-3 w-3" />
                            System Log
                        </span>
                        <div className="flex gap-1.5">
                            <div className="h-2.5 w-2.5 rounded-full bg-red-500/80" />
                            <div className="h-2.5 w-2.5 rounded-full bg-yellow-500/80" />
                            <div className="h-2.5 w-2.5 rounded-full bg-green-500/80" />
                        </div>
                    </div>
                    <ScrollArea className="flex-1 p-4" ref={scrollRef}>
                        <div className="space-y-1.5">
                            {logs.map((log, i) => (
                                <div key={i} className="opacity-90 hover:opacity-100 transition-opacity break-words leading-relaxed border-l-2 border-transparent hover:border-green-500/50 pl-2">
                                    <span className="text-green-700 mr-2 select-none">[{new Date().toLocaleTimeString('en-US', { hour12: false }).split(' ')[0]}]</span>
                                    <span className={log.includes('Error') ? 'text-red-400' : 'text-green-400'}>{log}</span>
                                </div>
                            ))}
                            {isProcessing && (
                                <div className="animate-pulse text-green-500/50 pt-2">_</div>
                            )}
                        </div>
                    </ScrollArea>
                </Card>
            </div>
        </div>
    );
};
