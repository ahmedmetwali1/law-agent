import React, { useState } from 'react';
import { Brain, Scale, Calendar, Activity, TrendingUp } from 'lucide-react';

type TabId = 'thinking' | 'memory' | 'deontic' | 'temporal' | 'analysis';

interface Tab {
    id: TabId;
    label: string;
    icon: React.FC<{ className?: string }>;
}

const tabs: Tab[] = [
    { id: 'thinking', label: 'التفكير', icon: Activity },
    { id: 'memory', label: 'الذاكرة', icon: Brain },
    { id: 'deontic', label: 'الواجبات', icon: Scale },
    { id: 'temporal', label: 'المواعيد', icon: Calendar },
    { id: 'analysis', label: 'التحليل', icon: TrendingUp },
];

interface ContextPanelProps {
    className?: string;
}

export const ContextPanel: React.FC<ContextPanelProps> = ({ className = '' }) => {
    const [activeTab, setActiveTab] = useState<TabId>('thinking');

    return (
        <div className={`flex flex-col bg-background border-t border-border ${className}`}>
            {/* Tabs */}
            <div className="flex border-b border-border bg-surface">
                {tabs.map((tab) => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.id;

                    return (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`
                                flex-1 flex items-center justify-center gap-2 py-3 px-4
                                transition-all duration-200 relative
                                ${isActive
                                    ? 'text-primary bg-background'
                                    : 'text-muted-foreground hover:text-foreground hover:bg-muted/30'
                                }
                            `}
                        >
                            {isActive && (
                                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
                            )}
                            <Icon className="h-4 w-4" />
                            <span className="text-sm font-medium">{tab.label}</span>
                        </button>
                    );
                })}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4">
                {activeTab === 'thinking' && <ThinkingTab />}
                {activeTab === 'memory' && <MemoryTab />}
                {activeTab === 'deontic' && <DeonticTab />}
                {activeTab === 'temporal' && <TemporalTab />}
                {activeTab === 'analysis' && <AnalysisTab />}
            </div>
        </div>
    );
};

// Tab Components
const ThinkingTab: React.FC = () => (
    <div className="space-y-3">
        <h3 className="text-lg font-semibold">عملية التفكير</h3>
        <div className="space-y-2">
            <ThinkingStep step="1" title="تحليل السؤال" status="completed" />
            <ThinkingStep step="2" title="تصنيف المجال" status="completed" />
            <ThinkingStep step="3" title="البحث في المعرفة" status="active" />
            <ThinkingStep step="4" title="بناء الإجابة" status="pending" />
        </div>
    </div>
);

const MemoryTab: React.FC = () => (
    <div className="space-y-3">
        <h3 className="text-lg font-semibold">نظام الذاكرة</h3>
        <div className="space-y-4">
            <MemorySection title="Working Memory" count={3} total={20} />
            <MemorySection title="Episodic Memory" count={5} />
            <MemorySection title="Long-term Memory" count={12} />
        </div>
    </div>
);

const DeonticTab: React.FC = () => (
    <div className="space-y-3">
        <h3 className="text-lg font-semibold">الواجبات القانونية</h3>
        <p className="text-sm text-muted-foreground">
            تحليل الواجبات والحقوق والمحظورات في القضية
        </p>
        <div className="text-center py-8 text-muted-foreground">
            لا توجد واجبات محددة بعد
        </div>
    </div>
);

const TemporalTab: React.FC = () => (
    <div className="space-y-3">
        <h3 className="text-lg font-semibold">المواعيد والمهل</h3>
        <p className="text-sm text-muted-foreground">
            المواعيد القانونية والمهل الزمنية
        </p>
        <div className="text-center py-8 text-muted-foreground">
            لا توجد مواعيد محددة بعد
        </div>
    </div>
);

const AnalysisTab: React.FC = () => (
    <div className="space-y-3">
        <h3 className="text-lg font-semibold">التحليل الشامل</h3>
        <p className="text-sm text-muted-foreground">
            معلومات تفصيلية عن عملية التحليل
        </p>
        <div className="text-center py-8 text-muted-foreground">
            ابدأ محادثة لرؤية التحليل
        </div>
    </div>
);

// Helper Components
interface ThinkingStepProps {
    step: string;
    title: string;
    status: 'completed' | 'active' | 'pending';
}

const ThinkingStep: React.FC<ThinkingStepProps> = ({ step, title, status }) => (
    <div className={`
        flex items-center gap-3 p-3 rounded-lg border
        ${status === 'completed' ? 'bg-success/5 border-success/20' :
            status === 'active' ? 'bg-primary/5 border-primary/20 animate-pulse-soft' :
                'bg-muted/30 border-border'}
    `}>
        <div className={`
            flex items-center justify-center w-8 h-8 rounded-full font-semibold text-sm
            ${status === 'completed' ? 'bg-success text-white' :
                status === 'active' ? 'bg-primary text-white' :
                    'bg-muted-foreground/20 text-muted-foreground'}
        `}>
            {step}
        </div>
        <span className="text-sm font-medium">{title}</span>
    </div>
);

interface MemorySectionProps {
    title: string;
    count: number;
    total?: number;
}

const MemorySection: React.FC<MemorySectionProps> = ({ title, count, total }) => (
    <div className="p-3 rounded-lg bg-muted/30 border border-border">
        <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">{title}</span>
            <span className="text-xs text-muted-foreground">
                {count}{total ? `/${total}` : ''}
            </span>
        </div>
        {total && (
            <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
                <div
                    className="h-full bg-gradient-to-r from-primary to-success"
                    style={{ width: `${(count / total) * 100}%` }}
                />
            </div>
        )}
    </div>
);
