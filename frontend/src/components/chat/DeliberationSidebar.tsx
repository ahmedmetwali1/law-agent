import React from 'react';
import { useChatStore } from '@/stores/chatStore';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, ShieldAlert, ShieldCheck, Brain, Gavel, Scale, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export const DeliberationSidebar: React.FC = () => {
    const { councilSession, hcfDecisions, currentActivity } = useChatStore();

    // Latest HCF Decision (if any)
    const latestHCF = hcfDecisions.length > 0 ? hcfDecisions[hcfDecisions.length - 1] : null;

    return (
        <div className="w-80 h-full bg-obsidian-900/90 backdrop-blur-xl border-r border-gold-500/10 flex flex-col shadow-2xl z-20 overflow-hidden">

            {/* Header */}
            <div className="p-4 border-b border-gold-500/10 bg-obsidian-950/50 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Scale className="w-5 h-5 text-gold-500" />
                    <h2 className="text-sm font-bold text-gold-100">غرفة المداولة</h2>
                </div>
                {currentActivity.isThinking && (
                    <div className="flex items-center gap-1.5 px-2 py-0.5 bg-blue-500/10 rounded-full border border-blue-500/20">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                        </span>
                        <span className="text-[10px] text-blue-400 font-medium">نشط</span>
                    </div>
                )}
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">

                {/* 1. HCF Status Card */}
                {latestHCF && (
                    <div className="space-y-2">
                        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider flex items-center gap-1">
                            <Shield className="w-3 h-3" />
                            حالة التحقق (HCF)
                        </div>

                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className={cn(
                                "p-3 rounded-lg border flex flex-col gap-2 relative overflow-hidden",
                                latestHCF.status === 'VERIFIED_SOURCE' ? "bg-emerald-500/10 border-emerald-500/30" :
                                    latestHCF.status === 'VERIFIED_ANALOGY' ? "bg-blue-500/10 border-blue-500/30" :
                                        "bg-amber-500/10 border-amber-500/30"
                            )}
                        >
                            <div className="flex items-start justify-between z-10">
                                <span className={cn(
                                    "text-xs font-bold px-2 py-0.5 rounded border",
                                    latestHCF.status === 'VERIFIED_SOURCE' ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30" :
                                        latestHCF.status === 'VERIFIED_ANALOGY' ? "bg-blue-500/20 text-blue-300 border-blue-500/30" :
                                            "bg-amber-500/20 text-amber-300 border-amber-500/30"
                                )}>
                                    {latestHCF.status === 'VERIFIED_SOURCE' ? 'نص صريح' :
                                        latestHCF.status === 'VERIFIED_ANALOGY' ? 'قياس منطقي' : 'تقدير استراتيجي'}
                                </span>
                                {latestHCF.confidence > 0 && (
                                    <span className="text-[10px] font-mono text-gray-400">
                                        {Math.round(latestHCF.confidence * 100)}% ثقة
                                    </span>
                                )}
                            </div>

                            <p className="text-xs text-gray-300 leading-relaxed z-10">
                                {latestHCF.path === 'DIRECT' ? 'تم العثور على مادة قانونية تطابق الطلب تماماً.' :
                                    latestHCF.path === 'ANALOGICAL' ? 'لا يوجد نص مباشر، تم البناء على سوابق مماثلة.' :
                                        'المسار غير واضح، يتم الاعتماد على القواعد العامة.'}
                            </p>

                            {/* Background Icon */}
                            <div className="absolute -bottom-4 -right-4 opacity-10 rotate-12">
                                {latestHCF.status === 'VERIFIED_SOURCE' ? <ShieldCheck className="w-24 h-24" /> :
                                    latestHCF.status === 'VERIFIED_ANALOGY' ? <Brain className="w-24 h-24" /> :
                                        <AlertTriangle className="w-24 h-24" />}
                            </div>
                        </motion.div>
                    </div>
                )}

                {/* 2. Council Monologues */}
                {councilSession.monologues.length > 0 && (
                    <div className="space-y-3">
                        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider flex items-center gap-1 sticky top-0 bg-obsidian-900/90 backdrop-blur py-2 z-10">
                            <Gavel className="w-3 h-3" />
                            محضر المجلس
                        </div>

                        <div className="space-y-3 pl-2 border-l border-gray-800">
                            <AnimatePresence mode='popLayout'>
                                {councilSession.monologues.map((entry) => (
                                    <motion.div
                                        key={entry.id}
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        layout
                                        className="relative"
                                    >
                                        {/* Dot on timeline */}
                                        <div className={cn(
                                            "absolute -left-[13px] top-2 w-2 h-2 rounded-full border-2 border-obsidian-900",
                                            entry.agent === 'legislator' ? "bg-emerald-500" :
                                                entry.agent === 'strategist' ? "bg-blue-500" :
                                                    "bg-rose-500"
                                        )} />

                                        <div className="bg-obsidian-800/50 rounded p-2 border border-gray-800/50">
                                            <div className="flex items-center justify-between mb-1">
                                                <span className={cn(
                                                    "text-[10px] font-bold uppercase",
                                                    entry.agent === 'legislator' ? "text-emerald-400" :
                                                        entry.agent === 'strategist' ? "text-blue-400" :
                                                            "text-rose-400"
                                                )}>
                                                    {entry.agent}
                                                </span>
                                                <span className="text-[9px] text-gray-600">
                                                    {new Date(entry.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                </span>
                                            </div>
                                            <p className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap">
                                                {entry.content}
                                            </p>
                                        </div>
                                    </motion.div>
                                ))}
                            </AnimatePresence>
                        </div>
                    </div>
                )}

                {/* Empty State */}
                {!latestHCF && councilSession.monologues.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-20 text-gray-600 text-center space-y-2 opacity-50">
                        <Scale className="w-10 h-10 mb-2" />
                        <p className="text-sm">المجلس في حالة انعقاد دائم</p>
                        <p className="text-[10px]">بانتظار القضية القادمة...</p>
                    </div>
                )}

            </div>
        </div>
    );
};
