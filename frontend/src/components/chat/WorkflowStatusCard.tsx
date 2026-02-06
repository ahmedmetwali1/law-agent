import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Circle, Loader2 } from 'lucide-react';

interface WorkflowStep {
    id: string;
    title: string;
    description?: string;
    status: 'pending' | 'active' | 'completed' | 'error';
    currentAction?: string;
}

interface WorkflowStatusCardProps {
    plan: WorkflowStep[];
    currentAction?: string; // Overall current action if not in step
    className?: string;
}

export const WorkflowStatusCard: React.FC<WorkflowStatusCardProps> = ({
    plan,
    currentAction,
    className = ""
}) => {
    if (!plan || plan.length === 0) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`bg-white/50 backdrop-blur-sm border border-gold-200/50 rounded-lg p-4 mb-4 shadow-sm ${className}`}
        >
            <h3 className="text-sm font-semibold text-gold-800 mb-3 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-gold-400 animate-pulse" />
                خطة العمل (10 دورات بحثية)
            </h3>

            <div className="space-y-4 relative">
                {/* Vertical Line */}
                <div className="absolute top-2 bottom-2 right-[11px] w-0.5 bg-gray-100 z-0" />

                {plan.map((step, idx) => (
                    <div key={idx} className="relative z-10 flex items-start gap-3">
                        <div className="flex-shrink-0 mt-0.5 bg-white">
                            {step.status === 'completed' && (
                                <CheckCircle2 className="w-6 h-6 text-green-500 fill-green-50" />
                            )}
                            {step.status === 'active' && (
                                <motion.div
                                    animate={{ rotate: 360 }}
                                    transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                                >
                                    <Loader2 className="w-6 h-6 text-gold-500" />
                                </motion.div>
                            )}
                            {step.status === 'pending' && (
                                <Circle className="w-6 h-6 text-gray-300" />
                            )}
                            {step.status === 'error' && (
                                <Circle className="w-6 h-6 text-red-400" />
                            )}
                        </div>

                        <div className="flex-1 min-w-0">
                            <h4 className={`text-sm font-medium ${step.status === 'active' ? 'text-gold-700' :
                                    step.status === 'completed' ? 'text-gray-700' : 'text-gray-400'
                                }`}>
                                {step.title}
                            </h4>

                            {/* Active Step Details */}
                            {step.status === 'active' && (step.currentAction || currentAction) && (
                                <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: 'auto' }}
                                    className="mt-1 text-xs text-gold-600 bg-gold-50/50 p-2 rounded border border-gold-100/50"
                                >
                                    {step.currentAction || currentAction}
                                </motion.div>
                            )}

                            {step.description && step.status !== 'pending' && step.status !== 'active' && (
                                <p className="text-xs text-gray-500 mt-0.5">{step.description}</p>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </motion.div>
    );
};
