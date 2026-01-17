import React from 'react';
import { useCaseStore } from '@/store';
import { Card, CardHeader, CardTitle, CardContent, Progress, Badge } from '@/components/ui';
import { CheckCircle2, Circle, Loader2, Clock } from 'lucide-react';

export const WorkflowProgress: React.FC = () => {
    const { currentCase, isProcessing } = useCaseStore();

    if (!currentCase) {
        return (
            <Card>
                <CardContent className="p-12 text-center text-muted-foreground">
                    <Clock className="h-16 w-16 mx-auto mb-4 opacity-20" />
                    <p>لا يوجد سير عمل نشط</p>
                </CardContent>
            </Card>
        );
    }

    const steps = [
        { name: 'استلام القضية', status: 'completed' },
        { name: 'التحليل الأولي', status: currentCase.analysis ? 'completed' : 'pending' },
        { name: 'إنشاء الخطة', status: currentCase.plan ? 'completed' : 'pending' },
        { name: 'تنفيذ الوكلاء', status: currentCase.specialist_reports?.length ? 'completed' : isProcessing ? 'current' : 'pending' },
        { name: 'التوصية النهائية', status: currentCase.final_recommendation ? 'completed' : 'pending' },
    ];

    const completedSteps = steps.filter(s => s.status === 'completed').length;
    const progressPercent = (completedSteps / steps.length) * 100;

    const getStepIcon = (status: string) => {
        if (status === 'completed') return <CheckCircle2 className="h-5 w-5 text-green-500" />;
        if (status === 'current') return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
        return <Circle className="h-5 w-5 text-muted-foreground" />;
    };

    return (
        <div className="space-y-6">
            {/* Overall Progress */}
            <Card>
                <CardHeader>
                    <CardTitle>📊 التقدم الإجمالي</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                            <span>اكتمل {completedSteps} من {steps.length} خطوات</span>
                            <span className="font-semibold">{progressPercent.toFixed(0)}%</span>
                        </div>
                        <Progress value={progressPercent} />
                    </div>
                </CardContent>
            </Card>

            {/* Timeline */}
            <Card>
                <CardHeader>
                    <CardTitle>🔄 سير العمل</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {steps.map((step, idx) => (
                            <div key={idx} className="flex items-start gap-3">
                                <div className="mt-0.5">{getStepIcon(step.status)}</div>
                                <div className="flex-1">
                                    <div className="flex items-center justify-between">
                                        <p className={`font-medium ${step.status === 'completed' ? 'text-foreground' : 'text-muted-foreground'}`}>
                                            {step.name}
                                        </p>
                                        {step.status === 'completed' && (
                                            <Badge variant="success" className="text-xs">✓ مكتمل</Badge>
                                        )}
                                        {step.status === 'current' && (
                                            <Badge variant="warning" className="text-xs">⏳ جاري...</Badge>
                                        )}
                                    </div>
                                    {idx < steps.length - 1 && (
                                        <div className="h-8 w-px bg-border ml-2 mt-2" />
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>

            {/* Agent Reports */}
            {currentCase.specialist_reports && currentCase.specialist_reports.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle>🤖 تقارير الوكلاء</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {currentCase.specialist_reports.map((report: any, idx: number) => (
                                <div key={idx} className="p-3 rounded-lg border">
                                    <div className="flex items-center justify-between mb-2">
                                        <div className="flex items-center gap-2">
                                            <Badge variant="success">✅</Badge>
                                            <span className="font-medium">{report.agent}</span>
                                        </div>
                                        {report.confidence && (
                                            <span className="text-xs text-muted-foreground">
                                                ثقة: {(report.confidence * 100).toFixed(0)}%
                                            </span>
                                        )}
                                    </div>
                                    <p className="text-sm text-muted-foreground">{report.expertise}</p>
                                    {report.knowledge_used && (
                                        <p className="text-xs text-muted-foreground mt-1">
                                            📚 استخدم {report.knowledge_used} مصدر من قاعدة المعرفة
                                        </p>
                                    )}
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
};
