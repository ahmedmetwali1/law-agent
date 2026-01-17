import { createContext, useContext, useState, ReactNode } from 'react'

interface BreadcrumbContextType {
    pageTitle: string | null
    setPageTitle: (title: string | null) => void
}

const BreadcrumbContext = createContext<BreadcrumbContextType>({
    pageTitle: null,
    setPageTitle: () => { },
})

export function BreadcrumbProvider({ children }: { children: ReactNode }) {
    const [pageTitle, setPageTitle] = useState<string | null>(null)

    return (
        <BreadcrumbContext.Provider value={{ pageTitle, setPageTitle }}>
            {children}
        </BreadcrumbContext.Provider>
    )
}

export const useBreadcrumb = () => useContext(BreadcrumbContext)
