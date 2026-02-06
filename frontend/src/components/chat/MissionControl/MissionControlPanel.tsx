import React from 'react';
import { Activity, Brain, ShieldCheck, History } from 'lucide-react';
import { motion } from 'framer-motion';
import { ExecutionTimeline, ExecutionStep } from './ExecutionTimeline';
import { cn } from '../../../lib/utils';

interface MissionControlPanelProps {
    plan: {
        strategy: string;
        steps: ExecutionStep[];
    } | null;
    sessionStatus?: string;
    onBackToHistory?: () => void;
}

export function MissionControlPanel({ plan, sessionStatus, onBackToHistory }: MissionControlPanelProps) {
    return (
        <div className="flex flex-col h-full bg-slate-950">
            {/* Header Info */}
            <div className="p-5 border-b border-slate-800/50 bg-gradient-to-br from-purple-500/5 to-transparent">
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-purple-500/20 rounded-xl shadow-lg shadow-purple-500/10">
                        <Activity className="w-5 h-5 text-purple-400" />
                    </div>
                    <div>
                        <h2 className="text-sm font-bold text-white tracking-tight">Mission Control</h2>
                        <p className="text-[10px] text-slate-500 uppercase tracking-widest font-mono">Agent Logic Center</p>
                    </div>
                </div>

                {/* Live Status Badge */}
                <div className="flex items-center justify-between px-3 py-2 bg-slate-900/60 rounded-lg border border-slate-800">
                    <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                        <span className="text-[11px] font-medium text-slate-300">
                            {sessionStatus || "جاهز للاستخدام"}
                        </span>
                    </div>
                    <ShieldCheck className="w-3.5 h-3.5 text-slate-600" />
                </div>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent">
                {plan ? (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.98 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.4 }}
                    >
                        <ExecutionTimeline plan={plan} />
                    </motion.div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-64 text-center space-y-4 opacity-40">
                        <div className="p-4 bg-slate-900 rounded-2xl border border-slate-800">
                            <Brain className="w-10 h-10 text-slate-600" />
                        </div>
                        <div className="space-y-1">
                            <p className="text-sm font-bold text-slate-400">في انتظار المهمة</p>
                            <p className="text-[11px] text-slate-500">قم بطرح سؤال لبدء عملية التخطيط</p>
                        </div>
                    </div>
                )}

                {/* Technical Audit Log Placeholder */}
                <div className="pt-4 border-t border-slate-900">
                    <div className="flex items-center justify-between mb-3 px-1">
                        <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">System Logs</h4>
                        <div className="w-8 h-[1px] bg-slate-800" />
                    </div>
                    <div className="space-y-2">
                        <LogEntry time="21:48:05" level="INFO" msg="Cognitive Layer Initialized" />
                        <LogEntry time="21:48:06" level="DEBUG" msg="Hydrating Session History" />
                    </div>
                </div>
            </div>

            {/* Bottom Actions */}
            <div className="p-4 border-t border-slate-800/50 bg-slate-900/20">
                <button
                    onClick={onBackToHistory}
                    className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs font-bold text-slate-400 hover:bg-slate-800 transition-colors"
                >
                    <History className="w-3.5 h-3.5" />
                    رجوع للسجل
                </button>
            </div>
        </div>
    );
}

function LogEntry({ time, level, msg }: { time: string, level: string, msg: string }) {
    return (
        <div className="flex gap-2 font-mono text-[9px] leading-tight">
            <span className="text-slate-600">[{time}]</span>
            <span className={cn(
                level === 'ERROR' ? 'text-rose-500' : 'text-blue-500'
            )}>{level}</span>
            <span className="text-slate-400 truncate">{msg}</span>
        </div>
    );
}
