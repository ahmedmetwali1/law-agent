import React from 'react';
import { CheckCircle, XCircle, Calendar, User, Scale, FileText, AlertCircle } from 'lucide-react';
import { CitationRenderer } from './CitationRenderer';

interface ToolResult {
    success: boolean;
    data?: any;
    count?: number;
    hearings?: any[];
    clients?: any[];
    cases?: any[];
    client?: any;
    case?: any;
    hearing?: any;
    profile?: any;
    error?: string;
    message?: string;
}

interface RichMessageProps {
    content: string;
    isUser: boolean;
}

export const RichMessage: React.FC<RichMessageProps> = ({ content, isUser }) => {
    // Try to detect if content contains structured data
    const tryParseJSON = (str: string): ToolResult | null => {
        try {
            // Check if string looks like JSON
            if (str.trim().startsWith('{') && str.trim().endsWith('}')) {
                return JSON.parse(str);
            }
        } catch {
            return null;
        }
        return null;
    };

    const data = tryParseJSON(content);

    // If it's user message or not JSON, show as normal text
    if (isUser || !data) {
        return (
            <div className="prose prose-sm dark:prose-invert max-w-none"
                style={{ fontFamily: 'Cairo, sans-serif' }}>
                <CitationRenderer text={content} />
            </div>
        );
    }

    // Render based on data type
    return (
        <div className="space-y-3">
            {/* Success/Error Badge */}
            {data.success !== undefined && (
                <div className={`flex items-center gap-2 p-3 rounded-lg ${data.success
                    ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300'
                    : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300'
                    }`}>
                    {data.success ? (
                        <CheckCircle className="h-5 w-5" />
                    ) : (
                        <XCircle className="h-5 w-5" />
                    )}
                    <span className="font-medium" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        {data.message || (data.success ? 'تم بنجاح' : 'حدث خطأ')}
                    </span>
                </div>
            )}

            {/* Hearings List */}
            {data.hearings && data.hearings.length > 0 && (
                <HearingsList hearings={data.hearings} />
            )}

            {/* Clients List */}
            {data.clients && data.clients.length > 0 && (
                <ClientsList clients={data.clients} />
            )}

            {/* Cases List */}
            {data.cases && data.cases.length > 0 && (
                <CasesList cases={data.cases} />
            )}

            {/* Single Client */}
            {data.client && (
                <ClientCard client={data.client} />
            )}

            {/* Single Case */}
            {data.case && (
                <CaseCard case={data.case} />
            )}

            {/* Single Hearing */}
            {data.hearing && (
                <HearingCard hearing={data.hearing} />
            )}

            {/* Profile */}
            {data.profile && (
                <ProfileCard profile={data.profile} />
            )}

            {/* Error Details */}
            {data.error && !data.success && (
                <div className="flex items-start gap-2 p-3 bg-red-50 dark:bg-red-900/10 rounded-lg border border-red-200 dark:border-red-800">
                    <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" />
                    <div className="flex-1">
                        <p className="text-sm text-red-700 dark:text-red-300" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            {data.error}
                        </p>
                    </div>
                </div>
            )}

            {/* Empty State */}
            {data.count === 0 && (
                <div className="text-center py-6 text-muted-foreground">
                    <p style={{ fontFamily: 'Cairo, sans-serif' }}>لا توجد نتائج</p>
                </div>
            )}
        </div>
    );
};

// Hearings List Component
const HearingsList: React.FC<{ hearings: any[] }> = ({ hearings }) => (
    <div className="space-y-2">
        <h4 className="font-semibold flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
            <Calendar className="h-4 w-4" />
            الجلسات ({hearings.length})
        </h4>
        {hearings.map((hearing, index) => (
            <div key={index} className="p-3 bg-blue-50 dark:bg-blue-900/10 rounded-lg border border-blue-200 dark:border-blue-800">
                <div className="flex items-start justify-between">
                    <div className="flex-1">
                        <p className="font-medium" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            {hearing.case_title || 'جلسة قضائية'}
                        </p>
                        <div className="mt-2 space-y-1 text-sm text-muted-foreground">
                            <p>📅 {new Date(hearing.hearing_date).toLocaleDateString('ar-SA')}</p>
                            <p>⏰ {hearing.hearing_time || 'غير محدد'}</p>
                            <p>⚖️ {hearing.court_name || 'غير محدد'}</p>
                        </div>
                    </div>
                </div>
            </div>
        ))}
    </div>
);

// Clients List Component
const ClientsList: React.FC<{ clients: any[] }> = ({ clients }) => (
    <div className="space-y-2">
        <h4 className="font-semibold flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
            <User className="h-4 w-4" />
            الموكلين ({clients.length})
        </h4>
        {clients.map((client, index) => (
            <div key={index} className="p-3 bg-purple-50 dark:bg-purple-900/10 rounded-lg border border-purple-200 dark:border-purple-800">
                <div className="flex items-start justify-between">
                    <div className="flex-1">
                        <p className="font-medium" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            {client.full_name}
                        </p>
                        <div className="mt-2 space-y-1 text-sm text-muted-foreground">
                            {client.phone && <p>📞 {client.phone}</p>}
                            {client.email && <p>📧 {client.email}</p>}
                            {client.address && <p>📍 {client.address}</p>}
                        </div>
                    </div>
                </div>
            </div>
        ))}
    </div>
);

// Cases List Component
const CasesList: React.FC<{ cases: any[] }> = ({ cases }) => (
    <div className="space-y-2">
        <h4 className="font-semibold flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
            <Scale className="h-4 w-4" />
            القضايا ({cases.length})
        </h4>
        {cases.map((caseItem, index) => (
            <div key={index} className="p-3 bg-orange-50 dark:bg-orange-900/10 rounded-lg border border-orange-200 dark:border-orange-800">
                <div className="flex items-start justify-between">
                    <div className="flex-1">
                        <p className="font-medium" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            {caseItem.case_title || caseItem.case_number}
                        </p>
                        <div className="mt-2 space-y-1 text-sm text-muted-foreground">
                            {caseItem.case_number && <p>📋 {caseItem.case_number}</p>}
                            {caseItem.court_name && <p>⚖️ {caseItem.court_name}</p>}
                            {caseItem.status && (
                                <span className={`inline-block px-2 py-0.5 rounded text-xs ${caseItem.status === 'active'
                                    ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                                    : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300'
                                    }`}>
                                    {caseItem.status === 'active' ? 'نشطة' : 'مغلقة'}
                                </span>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        ))}
    </div>
);

// Single Client Card
const ClientCard: React.FC<{ client: any }> = ({ client }) => (
    <div className="p-4 bg-gradient-to-br from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-xl border border-purple-200 dark:border-purple-800">
        <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-full flex items-center justify-center">
                <User className="h-6 w-6 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
                <h3 className="font-bold text-lg" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    {client.full_name}
                </h3>
                <p className="text-sm text-muted-foreground">موكل جديد</p>
            </div>
        </div>
        <div className="space-y-2 text-sm">
            {client.phone && (
                <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">📞</span>
                    <span>{client.phone}</span>
                </div>
            )}
            {client.email && (
                <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">📧</span>
                    <span>{client.email}</span>
                </div>
            )}
            {client.address && (
                <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">📍</span>
                    <span>{client.address}</span>
                </div>
            )}
        </div>
    </div>
);

// Single Case Card
const CaseCard: React.FC<{ case: any }> = ({ case: caseItem }) => (
    <div className="p-4 bg-gradient-to-br from-orange-50 to-yellow-50 dark:from-orange-900/20 dark:to-yellow-900/20 rounded-xl border border-orange-200 dark:border-orange-800">
        <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 bg-orange-100 dark:bg-orange-900/30 rounded-full flex items-center justify-center">
                <Scale className="h-6 w-6 text-orange-600 dark:text-orange-400" />
            </div>
            <div>
                <h3 className="font-bold text-lg" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    {caseItem.case_title || caseItem.case_number}
                </h3>
                <p className="text-sm text-muted-foreground">قضية جديدة</p>
            </div>
        </div>
        <div className="space-y-2 text-sm">
            {caseItem.case_number && (
                <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">📋</span>
                    <span>{caseItem.case_number}</span>
                </div>
            )}
            {caseItem.court_name && (
                <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">⚖️</span>
                    <span>{caseItem.court_name}</span>
                </div>
            )}
        </div>
    </div>
);

// Single Hearing Card
const HearingCard: React.FC<{ hearing: any }> = ({ hearing }) => (
    <div className="p-4 bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 rounded-xl border border-blue-200 dark:border-blue-800">
        <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
                <Calendar className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
                <h3 className="font-bold text-lg" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    {hearing.case_title || 'جلسة قضائية'}
                </h3>
                <p className="text-sm text-muted-foreground">جلسة جديدة</p>
            </div>
        </div>
        <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2">
                <span className="text-muted-foreground">📅</span>
                <span>{new Date(hearing.hearing_date).toLocaleDateString('ar-SA')}</span>
            </div>
            {hearing.hearing_time && (
                <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">⏰</span>
                    <span>{hearing.hearing_time}</span>
                </div>
            )}
            {hearing.court_name && (
                <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">⚖️</span>
                    <span>{hearing.court_name}</span>
                </div>
            )}
        </div>
    </div>
);

// Profile Card
const ProfileCard: React.FC<{ profile: any }> = ({ profile }) => (
    <div className="p-4 bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-xl border border-indigo-200 dark:border-indigo-800">
        <div className="flex items-center gap-3 mb-3">
            <div className="w-16 h-16 bg-indigo-100 dark:bg-indigo-900/30 rounded-full flex items-center justify-center">
                <User className="h-8 w-8 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div>
                <h3 className="font-bold text-xl" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    {profile.full_name}
                </h3>
                <p className="text-sm text-muted-foreground">{profile.role === 'lawyer' ? 'محامي' : 'مساعد'}</p>
            </div>
        </div>
        <div className="space-y-2 text-sm">
            {profile.email && (
                <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">📧</span>
                    <span>{profile.email}</span>
                </div>
            )}
            {profile.phone && (
                <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">📞</span>
                    <span>{profile.phone}</span>
                </div>
            )}
            {profile.created_at && (
                <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">📅</span>
                    <span>مسجل منذ {new Date(profile.created_at).toLocaleDateString('ar-SA')}</span>
                </div>
            )}
        </div>
    </div>
);
