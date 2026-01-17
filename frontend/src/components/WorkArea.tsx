import React, { useEffect } from 'react';
import { useUIStore, useCaseStore } from '@/store';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui';
import { CaseOverview } from '@/components/CaseOverview';
import { WorkflowProgress } from '@/components/WorkflowProgress';
import { PlanViewer } from '@/components/PlanViewer';
import { FinalResults } from '@/components/FinalResults';
import { LayoutGrid, Activity, FileCheck, FileText, Scale } from 'lucide-react';

export const WorkArea: React.FC = () => {
    const { activeTab, setActiveTab } = useUIStore();
    const { currentCase, isProcessing } = useCaseStore();

    // Auto-switch to progress tab when processing starts
    useEffect(() => {
        if (isProcessing) {
            setActiveTab('progress');
        }
    }, [isProcessing, setActiveTab]);

    const tabs = [
        { value: 'overview', label: 'نظرة عامة', icon: LayoutGrid },
        { value: 'progress', label: 'التقدم', icon: Activity },
        { value: 'results', label: 'النتائج', icon: FileCheck },
    ];

    return (
        <div className="flex h-full flex-col bg-background">
            {/* Header - Modern Minimal */}
            <div className="border-b p-4 bg-muted/30">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                            <Scale className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                            <h1 className="text-lg font-bold">لوحة المخرجات</h1>
                            <p className="text-xs text-muted-foreground">
                                نتائج الدراسة القانونية
                            </p>
                        </div>
                    </div>
                    {isProcessing && (
                        <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full animate-pulse">
                            جاري المعالجة...
                        </span>
                    )}
                </div>
            </div>

            {/* Tabs Navigation */}
            <div className="border-b px-4 bg-muted/20">
                <Tabs value={activeTab} onValueChange={(val) => setActiveTab(val as any)}>
                    <TabsList className="w-full justify-start gap-1 bg-transparent py-0">
                        {tabs.map((tab) => (
                            <TabsTrigger
                                key={tab.value}
                                value={tab.value}
                                active={activeTab === tab.value}
                                onClick={() => setActiveTab(tab.value as any)}
                                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-all border-b-2 rounded-none ${activeTab === tab.value
                                    ? 'border-primary text-primary bg-transparent'
                                    : 'border-transparent text-muted-foreground hover:text-foreground'
                                    }`}
                            >
                                <tab.icon className="h-4 w-4" />
                                {tab.label}
                            </TabsTrigger>
                        ))}
                    </TabsList>
                </Tabs>
            </div>

            {/* Content Area - Canvas Style */}
            <div className="flex-1 overflow-y-auto p-6 bg-muted/10">
                {/* Empty State */}
                {!currentCase && !isProcessing && (
                    <div className="flex items-center justify-center h-full">
                        <div className="text-center max-w-md">
                            <div className="h-16 w-16 rounded-2xl bg-muted/50 flex items-center justify-center mx-auto mb-4">
                                <FileText className="h-8 w-8 text-muted-foreground" />
                            </div>
                            <h3 className="font-semibold text-lg mb-2">لا توجد دراسة حالية</h3>
                            <p className="text-sm text-muted-foreground">
                                ابدأ محادثة في منطقة الدردشة لإنشاء دراسة قانونية جديدة.
                                ستظهر المخرجات والتوصيات هنا.
                            </p>
                        </div>
                    </div>
                )}

                {/* Tab Contents */}
                {(currentCase || isProcessing) && (
                    <>
                        <TabsContent value="overview" active={activeTab === 'overview'}>
                            <CaseOverview />
                        </TabsContent>

                        <TabsContent value="progress" active={activeTab === 'progress'}>
                            <div className="space-y-6">
                                {/* Streaming Plan Viewer */}
                                <PlanViewer />

                                {/* Static Progress History (Optional) */}
                                {currentCase && !isProcessing && (
                                    <WorkflowProgress />
                                )}
                            </div>
                        </TabsContent>

                        <TabsContent value="results" active={activeTab === 'results'}>
                            <FinalResults />
                        </TabsContent>
                    </>
                )}
            </div>
        </div>
    );
};
