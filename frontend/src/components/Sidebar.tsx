import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Scale, MessageSquare, Users, Calendar } from 'lucide-react';

export const Sidebar: React.FC = () => {
    const location = useLocation();

    const menuItems = [
        { path: '/chat', icon: MessageSquare, label: 'المحادثة', color: 'bg-blue-600' },
        { path: '/clients', icon: Users, label: 'الموكلين', color: 'bg-green-600' },
        { path: '/hearings', icon: Calendar, label: 'الجلسات', color: 'bg-purple-600' },
    ];

    return (
        <div className="w-20 bg-white border-l border-gray-200 flex flex-col items-center py-6 gap-4 shadow-sm">
            {/* Logo */}
            <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-green-600 rounded-xl flex items-center justify-center mb-4 shadow-md">
                <Scale className="h-6 w-6 text-white" />
            </div>

            {/* Menu Items */}
            <nav className="flex-1 flex flex-col gap-3 w-full px-3">
                {menuItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = location.pathname === item.path;

                    return (
                        <Link
                            key={item.path}
                            to={item.path}
                            className={`
                                relative w-14 h-14 rounded-xl flex items-center justify-center
                                transition-all duration-300 group
                                ${isActive
                                    ? `${item.color} text-white shadow-lg scale-105`
                                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200 hover:text-gray-800 hover:scale-105'
                                }
                            `}
                            title={item.label}
                        >
                            {/* Active indicator */}
                            {isActive && (
                                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-white rounded-r-full" />
                            )}

                            <Icon className={`h-6 w-6 ${isActive ? 'animate-pulse' : ''}`} />

                            {/* Tooltip */}
                            <div className="absolute left-full ml-3 px-3 py-1.5 bg-gray-900 text-white text-sm rounded-lg
                                          opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
                                {item.label}
                            </div>
                        </Link>
                    );
                })}
            </nav>
        </div>
    );
};
