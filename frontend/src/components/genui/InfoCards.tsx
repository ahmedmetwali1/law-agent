
import React from 'react';
import { Info, AlertTriangle, CheckCircle, Shield } from 'lucide-react';

interface InfoCardItem {
    label: string;
    value: string;
    icon?: 'info' | 'warning' | 'success' | 'shield';
    color?: string;
}

interface InfoCardsProps {
    data: {
        title?: string;
        items: InfoCardItem[];
    }
}

const IconMap = {
    info: Info,
    warning: AlertTriangle,
    success: CheckCircle,
    shield: Shield
};

export const InfoCards: React.FC<InfoCardsProps> = ({ data }) => {
    return (
        <div className="my-4 space-y-3">
            {data.title && <h3 className="text-sm font-medium text-gray-400 px-1">{data.title}</h3>}
            <div className="grid gap-3 sm:grid-cols-2">
                {data.items.map((item, idx) => {
                    const Icon = item.icon ? IconMap[item.icon] : Info;

                    return (
                        <div key={idx} className="flex items-start gap-3 rounded-lg border border-[#3d4450] bg-[#252a30] p-3 transition-all hover:bg-[#2d3136]">
                            <div className={`mt-0.5 rounded-full bg-[#1e2227] p-1.5 ${item.icon === 'warning' ? 'text-yellow-500' :
                                    item.icon === 'success' ? 'text-green-500' :
                                        item.icon === 'shield' ? 'text-[#2a8f7a]' : 'text-blue-500'
                                }`}>
                                <Icon className="h-4 w-4" />
                            </div>
                            <div>
                                <h4 className="text-xs font-medium text-gray-400 mb-0.5">{item.label}</h4>
                                <p className="text-sm font-semibold text-white">{item.value}</p>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};
