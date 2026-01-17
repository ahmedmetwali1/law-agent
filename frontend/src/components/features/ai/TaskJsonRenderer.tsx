import { motion } from 'framer-motion'
import { CheckCircle, Clock, XCircle, Loader, Edit, Check } from 'lucide-react'
import { TaskSchema } from '../../../stores/chatStore'

interface TaskJsonRendererProps {
    taskJson: TaskSchema
    onConfirm?: () => void
    onEdit?: () => void
}

export function TaskJsonRenderer({ taskJson, onConfirm, onEdit }: TaskJsonRendererProps) {
    const statusConfig = {
        pending: {
            icon: Clock,
            color: 'text-gray-400',
            bgColor: 'bg-gray-400/10',
            label: 'قيد الانتظار'
        },
        in_progress: {
            icon: Loader,
            color: 'text-cobalt-500',
            bgColor: 'bg-cobalt-500/10',
            label: 'جاري التنفيذ'
        },
        completed: {
            icon: CheckCircle,
            color: 'text-success',
            bgColor: 'bg-success/10',
            label: 'مكتمل'
        },
        failed: {
            icon: XCircle,
            color: 'text-error',
            bgColor: 'bg-error/10',
            label: 'فشل'
        },
    }

    const config = statusConfig[taskJson.status]
    const StatusIcon = config.icon

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
            className="mt-3 glass-card p-4 border border-gold-500/30"
        >
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <StatusIcon
                        className={`w-5 h-5 ${config.color} ${taskJson.status === 'in_progress' ? 'animate-spin' : ''}`}
                    />
                    <h3 className="font-semibold text-white">{taskJson.task_type}</h3>
                </div>

                <span className={`text-xs px-3 py-1 rounded-full ${config.bgColor} ${config.color} font-medium`}>
                    {config.label}
                </span>
            </div>

            {/* Steps Progress */}
            <div className="space-y-2 mb-4">
                {taskJson.steps.map((step) => (
                    <div
                        key={step.step_number}
                        className="flex items-start gap-3 text-sm"
                    >
                        <div className={`
              w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-xs
              ${step.status === 'completed'
                                ? 'bg-success/20 text-success'
                                : step.status === 'in_progress'
                                    ? 'bg-cobalt-500/20 text-cobalt-500'
                                    : 'bg-obsidian-700 text-gray-400'
                            }
            `}>
                            {step.status === 'completed' ? '✓' : step.step_number}
                        </div>

                        <span className={
                            step.status === 'completed'
                                ? 'text-gray-300'
                                : step.status === 'in_progress'
                                    ? 'text-white'
                                    : 'text-gray-500'
                        }>
                            {step.description}
                        </span>
                    </div>
                ))}
            </div>

            {/* Action Buttons (only if pending or in_progress) */}
            {(taskJson.status === 'pending' || taskJson.status === 'in_progress') && (
                <div className="flex gap-2 pt-3 border-t border-gold-500/10">
                    <button
                        onClick={onConfirm}
                        className="flex-1 flex items-center justify-center gap-2 bg-cobalt-600 hover:bg-cobalt-500 text-white px-4 py-2 rounded-lg transition-all font-medium"
                    >
                        <Check className="w-4 h-4" />
                        <span>تأكيد</span>
                    </button>

                    <button
                        onClick={onEdit}
                        className="flex items-center justify-center gap-2 bg-transparent hover:bg-obsidian-700 text-gold-500 border border-gold-500/50 px-4 py-2 rounded-lg transition-all"
                    >
                        <Edit className="w-4 h-4" />
                        <span>تعديل</span>
                    </button>
                </div>
            )}
        </motion.div>
    )
}
