
import React from 'react';
import { Scale } from 'lucide-react';

interface ComparisonRow {
    feature: string;
    optionA: string;
    optionB: string;
    winner?: 'A' | 'B' | 'tie';
}

interface ComparisonTableProps {
    data: {
        title?: string;
        optionAlabel: string;
        optionBlabel: string;
        rows: ComparisonRow[];
    }
}

export const ComparisonTable: React.FC<ComparisonTableProps> = ({ data }) => {
    return (
        <div className="my-4 overflow-hidden rounded-xl border border-[#3d4450] bg-[#252a30]">
            {data.title && (
                <div className="flex items-center gap-2 border-b border-[#3d4450] bg-[#1e2227] p-4">
                    <Scale className="h-5 w-5 text-[#2a8f7a]" />
                    <h3 className="font-semibold text-white">{data.title}</h3>
                </div>
            )}

            <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                    <thead className="bg-[#2d3136] text-xs uppercase text-gray-400">
                        <tr>
                            <th className="px-4 py-3 text-right">المعيار</th>
                            <th className="px-4 py-3 text-right text-white">{data.optionAlabel}</th>
                            <th className="px-4 py-3 text-right text-white">{data.optionBlabel}</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-[#3d4450]">
                        {data.rows.map((row, idx) => (
                            <tr key={idx} className="hover:bg-[#2d3136]/50">
                                <td className="whitespace-nowrap px-4 py-3 font-medium text-gray-300">
                                    {row.feature}
                                </td>
                                <td className={`px-4 py-3 ${row.winner === 'A' ? 'text-green-400 font-medium' : 'text-gray-400'}`}>
                                    {row.optionA}
                                </td>
                                <td className={`px-4 py-3 ${row.winner === 'B' ? 'text-green-400 font-medium' : 'text-gray-400'}`}>
                                    {row.optionB}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
