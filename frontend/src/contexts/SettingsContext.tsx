import React, { createContext, useContext, useEffect, useState } from 'react';
import { apiClient } from '../api/client';

export interface PublicSettings {
    platform_name?: string;
    platform_name_en?: string;
    platform_description?: string;
    platform_logo_url?: string;
    platform_favicon_url?: string;
    footer_copyright_text?: string;
    footer_powered_by?: string;
    footer_links?: string | Array<{ text: string, url: string }>;
    contact_email?: string;
    contact_phone?: string;
    contact_whatsapp?: string;
    support_hours?: string;
    default_language?: string;
    currency?: string;
}

interface SettingsContextType {
    settings: PublicSettings;
    loading: boolean;
    refreshSettings: () => Promise<void>;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export function SettingsProvider({ children }: { children: React.ReactNode }) {
    const [settings, setSettings] = useState<PublicSettings>({});
    const [loading, setLoading] = useState(true);

    const fetchSettings = async () => {
        try {
            const data = await apiClient.get<PublicSettings>('/api/settings/public');
            setSettings(data || {});

            // Dynamic Favicon (if implemented)
            if (data?.platform_favicon_url) {
                const link: HTMLLinkElement | null = document.querySelector("link[rel*='icon']") || document.createElement('link');
                link.type = 'image/x-icon';
                link.rel = 'shortcut icon';
                link.href = data.platform_favicon_url;
                document.getElementsByTagName('head')[0].appendChild(link);
            }

        } catch (error) {
            console.error('Failed to fetch public settings', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSettings();
    }, []);

    return (
        <SettingsContext.Provider value={{ settings, loading, refreshSettings: fetchSettings }}>
            {children}
        </SettingsContext.Provider>
    );
}

export function useSettings() {
    const context = useContext(SettingsContext);
    if (context === undefined) {
        throw new Error('useSettings must be used within a SettingsProvider');
    }
    return context;
}
