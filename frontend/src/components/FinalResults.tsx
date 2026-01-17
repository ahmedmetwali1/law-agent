import React from 'react';
import { useCaseStore } from '@/store';
import { Card, CardHeader, CardTitle, CardContent, Badge } from '@/components/ui';
import { FileCheck, AlertTriangle, Scale, Download } from 'lucide-react';

export const FinalResults: React.FC = () => {
    const { currentCase } = useCaseStore();

    if (!currentCase?.final_recommendation) {
        return (
            <Card>
                <CardContent className="p-12 text-center text-muted-foreground">
                    <FileCheck className="h-16 w-16 mx-auto mb-4 opacity-20" />
                    <p>لا توجد نتائج نهائية بعد</p>
                    <p className="text-sm mt-2">سيتم عرض التوصية النهائية هنا بعد اكتمال التحليل</p>
                </CardContent>
            </Card>
        );
    }

    const recommendation = currentCase.final_recommendation;

    return (
        <div className="space-y-6">
            {/* Header */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div>
                            <CardTitle className="flex items-center gap-2">
                                <Scale className="h-6 w-6" />
                                التوصية القانونية النهائية
                            </CardTitle>
                            <p className="text-sm text-muted-foreground mt-1">
                                بناءً على تحليل {currentCase.specialist_reports?.length || 0} وكلاء متخصصين
                            </p>
                        </div>
                        <Badge variant={recommendation.confidence === 'عالية' ? 'success' : 'warning'}>
                            ثقة: {recommendation.confidence}
                        </Badge>
                    </div>
                </CardHeader>
            </Card>

            {/* Recommendation Text */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-lg">📋 التوصية</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="prose prose-sm max-w-none" dir="rtl">
                        <div className="whitespace-pre-wrap text-sm leading-relaxed">
                            {recommendation.recommendation_text}
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Summary Stats */}
            <div className="grid grid-cols-3 gap-4">
                <Card>
                    <CardContent className="p-4">
                        <div className="text-center">
                            <p className="text-2xl font-bold text-primary">
                                {currentCase.specialist_reports?.length || 0}
                            </p>
                            <p className="text-sm text-muted-foreground mt-1">وكلاء متخصصين</p>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-4">
                        <div className="text-center">
                            <p className="text-2xl font-bold text-green-500">✓</p>
                            <p className="text-sm text-muted-foreground mt-1">تحليل مكتمل</p>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-4">
                        <div className="text-center">
                            <p className="text-2xl font-bold text-blue-500">
                                {recommendation.confidence}
                            </p>
                            <p className="text-sm text-muted-foreground mt-1">درجة الثقة</p>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Actions */}
            <Card>
                <CardContent className="p-4">
                    <div className="flex gap-2">
                        <button className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors">
                            <Download className="h-4 w-4" />
                            تحميل التقرير PDF
                        </button>
                        <button className="flex items-center gap-2 px-4 py-2 border rounded-md hover:bg-accent transition-colors">
                            <FileCheck className="h-4 w-4" />
                            حفظ في الأرشيف
                        </button>
                    </div>
                </CardContent>
            </Card>

            {/* Case File Location */}
            {currentCase.case_file_path && (
                <Card>
                    <CardContent className="p-4">
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <FileCheck className="h-4 w-4" />
                            <span>ملف القضية محفوظ في:</span>
                            <code className="text-xs bg-muted px-2 py-1 rounded">
                                {currentCase.case_file_path}
                            </code>
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
};
