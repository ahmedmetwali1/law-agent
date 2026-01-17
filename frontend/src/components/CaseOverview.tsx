import React from 'react';
import { useCaseStore } from '@/store';
import { Card, CardHeader, CardTitle, CardContent, Badge } from '@/components/ui';
import { FileText, Calendar, User, Scale } from 'lucide-react';

export const CaseOverview: React.FC = () => {
    const { currentCase } = useCaseStore();

    if (!currentCase) {
        return (
            <Card>
                <CardContent className="p-12 text-center">
                    <div className="text-muted-foreground">
                        <Scale className="h-16 w-16 mx-auto mb-4 opacity-20" />
                        <p className="text-lg">لا توجد قضية محملة</p>
                        <p className="text-sm mt-2">ابدأ بإنشاء قضية جديدة من خلال الدردشة</p>
                    </div>
                </CardContent>
            </Card>
        );
    }

    const getStatusBadge = (status: string) => {
        const statusMap: Record<string, { variant: any; text: string }> = {
            pending: { variant: 'default', text: '⏳ قيد الانتظار' },
            analyzing: { variant: 'info', text: '🔍 قيد التحليل' },
            processing: { variant: 'warning', text: '⚙️ قيد المعالجة' },
            completed: { variant: 'success', text: '✅ مكتملة' },
            failed: { variant: 'error', text: '❌ فشلت' },
        };

        const statusInfo = statusMap[status] || statusMap.pending;
        return <Badge variant={statusInfo.variant}>{statusInfo.text}</Badge>;
    };

    return (
        <div className="space-y-4">
            {/* Case Header */}
            <Card>
                <CardHeader>
                    <div className="flex items-start justify-between">
                        <div>
                            <CardTitle className="flex items-center gap-2">
                                <FileText className="h-6 w-6" />
                                نظرة عامة على القضية
                            </CardTitle>
                            <p className="text-sm text-muted-foreground mt-1">
                                معرف القضية: {currentCase.case_id}
                            </p>
                        </div>
                        {getStatusBadge(currentCase.status)}
                    </div>
                </CardHeader>

                <CardContent>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="flex items-center gap-2 text-sm">
                            <User className="h-4 w-4 text-muted-foreground" />
                            <div>
                                <p className="text-muted-foreground">العميل</p>
                                <p className="font-medium">عميل جديد</p>
                            </div>
                        </div>

                        <div className="flex items-center gap-2 text-sm">
                            <Calendar className="h-4 w-4 text-muted-foreground" />
                            <div>
                                <p className="text-muted-foreground">تاريخ الإنشاء</p>
                                <p className="font-medium">الآن</p>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Initial Analysis */}
            {currentCase.analysis && (
                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg">🎯 التحليل الأولي</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            <div>
                                <p className="text-sm font-medium text-muted-foreground">نوع القضية</p>
                                <p className="text-lg font-semibold">
                                    {currentCase.analysis.case_classification || 'غير محدد'}
                                </p>
                            </div>

                            {currentCase.analysis.key_legal_points && (
                                <div>
                                    <p className="text-sm font-medium text-muted-foreground mb-2">
                                        النقاط القانونية الرئيسية
                                    </p>
                                    <ul className="list-disc list-inside space-y-1">
                                        {currentCase.analysis.key_legal_points.map((point: string, idx: number) => (
                                            <li key={idx} className="text-sm">{point}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {currentCase.analysis.preliminary_strength && (
                                <div>
                                    <p className="text-sm font-medium text-muted-foreground">قوة القضية الأولية</p>
                                    <Badge variant={
                                        currentCase.analysis.preliminary_strength === 'قوي' ? 'success' :
                                            currentCase.analysis.preliminary_strength === 'متوسط' ? 'warning' : 'default'
                                    }>
                                        {currentCase.analysis.preliminary_strength}
                                    </Badge>
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Plan Summary */}
            {currentCase.plan && (
                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg">📋 خطة العمل</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            <div>
                                <p className="text-sm text-muted-foreground">عدد الوكلاء المطلوبين</p>
                                <p className="text-2xl font-bold">
                                    {currentCase.plan.required_agents?.length || 0}
                                </p>
                            </div>

                            <div>
                                <p className="text-sm text-muted-foreground mb-2">الوكلاء</p>
                                <div className="space-y-2">
                                    {currentCase.plan.required_agents?.map((agent: any, idx: number) => (
                                        <div key={idx} className="flex items-center justify-between p-2 rounded-md border">
                                            <div>
                                                <p className="font-medium text-sm">{agent.type}</p>
                                                <p className="text-xs text-muted-foreground">{agent.focus}</p>
                                            </div>
                                            <Badge variant="default">أولوية {agent.priority}</Badge>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
};
