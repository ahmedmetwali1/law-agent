import React from 'react';
import { MissionControlPanel } from './MissionControl/MissionControlPanel';
import { ExecutionStep } from './MissionControl/ExecutionTimeline';

export type { ExecutionStep as PlanStep };

interface MissionControlProps {
    plan: ExecutionStep[];
    strategy?: string;
    sessionStatus?: string;
    onBackToHistory?: () => void;
}

export const MissionControl: React.FC<MissionControlProps> = ({ plan, strategy, sessionStatus, onBackToHistory }) => {
    return <MissionControlPanel
        plan={plan ? { strategy: strategy || '', steps: plan } : null}
        sessionStatus={sessionStatus}
        onBackToHistory={onBackToHistory}
    />;
};
