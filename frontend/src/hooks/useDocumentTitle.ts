import { useEffect } from 'react';
import { useSettings } from '../contexts/SettingsContext';
import { useBreadcrumb } from '../contexts/BreadcrumbContext';

export function useDocumentTitle() {
    const { settings } = useSettings();
    const { pageTitle } = useBreadcrumb();

    useEffect(() => {
        const platformName = settings.platform_name || 'Legal AI';

        if (pageTitle) {
            document.title = `${platformName} | ${pageTitle}`;
        } else {
            document.title = platformName;
        }
    }, [pageTitle, settings.platform_name]);
}
