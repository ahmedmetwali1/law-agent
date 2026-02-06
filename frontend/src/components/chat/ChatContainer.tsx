import React, { ReactNode } from 'react';

interface ChatContainerProps {
    children: ReactNode;
    sidebar?: ReactNode;
    header?: ReactNode;
    inputArea?: ReactNode;
    isWorksheetOpen?: boolean;
}

export const ChatContainer: React.FC<ChatContainerProps> = ({
    children,
    sidebar,
    header,
    inputArea,
    isWorksheetOpen = false
}) => {
    return (
        <div className={`flex h-[calc(100vh-8rem)] bg-obsidian-950 rounded-3xl overflow-hidden border border-gray-800 text-sm shadow-2xl relative transition-all duration-300 ${isWorksheetOpen ? 'ml-96' : ''}`}>

            {/* Sidebar (Optional) */}
            {sidebar && (
                <aside className="hidden md:flex flex-col w-80 border-l border-gray-800 bg-obsidian-900/50 backdrop-blur-md z-10">
                    {sidebar}
                </aside>
            )}

            {/* Main Content Area */}
            <main className="flex-1 flex flex-col relative bg-gradient-to-br from-obsidian-950 to-gray-900">

                {/* Header */}
                {header && (
                    <header className="h-16 border-b border-gray-800 bg-obsidian-900/80 backdrop-blur-md flex items-center justify-between px-6 shadow-sm z-20">
                        {header}
                    </header>
                )}

                {/* Messages Scroll Area (Children) */}
                <div className="flex-1 overflow-hidden relative">
                    <div className="absolute inset-0 flex flex-col">
                        {children}
                    </div>
                </div>

                {/* Input Area (Bottom Fixed) */}
                {inputArea && (
                    <footer className="p-4 bg-obsidian-900 border-t border-gray-800 z-20">
                        {inputArea}
                    </footer>
                )}
            </main>
        </div>
    );
};
