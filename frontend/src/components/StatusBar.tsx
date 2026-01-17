import React from 'react';
import { Brain, Zap, Scale, Calendar, Activity, LogOut, User } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface StatusBarProps {
    memoryItems?: number;
    memoryCapacity?: number;
    reasoningMode?: 'hybrid' | 'cot' | 'react';
    deonticActive?: boolean;
    temporalActive?: boolean;
    thinkingSpeed?: 'fast' | 'slow';
}

export const StatusBar: React.FC<StatusBarProps> = ({
    memoryItems = 0,
    memoryCapacity = 20,
    reasoningMode = 'hybrid',
    deonticActive = true,
    temporalActive = true,
    thinkingSpeed = 'slow'
}) => {
    const { user, logout } = useAuth();
    const memoryPercentage = (memoryItems / memoryCapacity) * 100;

    return (
        <div className="h-12 bg-surface border-b border-border px-4 flex items-center justify-between">
            {/* Left: System Status */}
            <div className="flex items-center gap-4">
                {/* Memory */}
                <div className="flex items-center gap-2">
                    <Brain className="h-4 w-4 text-primary" />
                    <span className="text-sm text-muted-foreground">ذاكرة:</span>
                    <div className="flex items-center gap-1.5">
                        <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-primary to-success transition-all duration-300"
                                style={{ width: `${memoryPercentage}%` }}
                            />
                        </div>
                        <span className="text-xs text-foreground font-medium">
                            {memoryItems}/{memoryCapacity}
                        </span>
                    </div>
                </div>

                {/* Reasoning Mode */}
                <div className="flex items-center gap-2 px-2 py-1 bg-muted/50 rounded-lg">
                    <Zap className="h-3.5 w-3.5 text-warning" />
                    <span className="text-xs text-muted-foreground">النمط:</span>
                    <span className="text-xs font-semibold text-foreground capitalize">
                        {reasoningMode}
                    </span>
                </div>

                {/* Thinking Speed */}
                <div className="flex items-center gap-2">
                    <Activity className={`h-3.5 w-3.5 ${thinkingSpeed === 'slow' ? 'text-info animate-pulse-soft' : 'text-success'}`} />
                    <span className="text-xs text-muted-foreground">
                        {thinkingSpeed === 'slow' ? 'تفكير عميق' : 'تفكير سريع'}
                    </span>
                </div>
            </div>

            {/* Right: Logic Systems + User Info */}
            <div className="flex items-center gap-3">
                {/* Deontic Logic */}
                <div className={`flex items-center gap-1.5 px-2 py-1 rounded-lg transition-all ${deonticActive ? 'bg-success/10 border border-success/20' : 'bg-muted/30'
                    }`}>
                    <Scale className={`h-3.5 w-3.5 ${deonticActive ? 'text-success' : 'text-muted-foreground'}`} />
                    <span className={`text-xs font-medium ${deonticActive ? 'text-success' : 'text-muted-foreground'}`}>
                        منطق الواجبات
                    </span>
                    {deonticActive && <div className="status-indicator success" />}
                </div>

                {/* Temporal Logic */}
                <div className={`flex items-center gap-1.5 px-2 py-1 rounded-lg transition-all ${temporalActive ? 'bg-info/10 border border-info/20' : 'bg-muted/30'
                    }`}>
                    <Calendar className={`h-3.5 w-3.5 ${temporalActive ? 'text-info' : 'text-muted-foreground'}`} />
                    <span className={`text-xs font-medium ${temporalActive ? 'text-info' : 'text-muted-foreground'}`}>
                        منطق المواعيد
                    </span>
                    {temporalActive && <div className="status-indicator info" />}
                </div>

                {/* User Info + Logout */}
                <div className="flex items-center gap-2 px-3 py-1 bg-muted/50 rounded-lg">
                    <User className="h-4 w-4 text-primary" />
                    <span className="text-sm font-medium text-foreground">
                        {user?.full_name || user?.email}
                    </span>
                    <button
                        onClick={logout}
                        className="p-1 hover:bg-destructive/10 rounded transition-colors"
                        title="تسجيل الخروج"
                    >
                        <LogOut className="h-4 w-4 text-destructive" />
                    </button>
                </div>
            </div>
        </div>
    );
};

