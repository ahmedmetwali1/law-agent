import { apiClient } from '../api/client'

export interface SearchResult {
    type: 'case' | 'client' | 'opponent' | 'authorization'
    id: string
    title: string
    subtitle?: string
    path: string
    icon: string
}

export async function globalSearch(query: string, lawyerId: string): Promise<SearchResult[]> {
    if (!query || query.trim().length < 2) {
        return []
    }

    const trimmedQuery = query.trim()
    const results: SearchResult[] = []

    try {
        // 1. Search Cases
        const casesResponse = await apiClient.get(`/api/cases/search?q=${trimmedQuery}`)
        if (casesResponse.success && casesResponse.cases) {
            casesResponse.cases.forEach((c: any) => {
                results.push({
                    type: 'case',
                    id: c.id,
                    title: `قضية ${c.case_number}`,
                    subtitle: c.subject || c.court_name,
                    path: `/cases/${c.id}`,
                    icon: '⚖️'
                })
            })
        }

        // 2. Search Clients
        const clientsResponse = await apiClient.get(`/api/clients/search?q=${trimmedQuery}`)
        if (clientsResponse.success && clientsResponse.clients) {
            clientsResponse.clients.forEach((client: any) => {
                results.push({
                    type: 'client',
                    id: client.id,
                    title: client.full_name,
                    subtitle: client.phone || client.email,
                    path: `/clients/${client.id}`,
                    icon: '👤'
                })
            })
        }

        return results
    } catch (error) {
        console.error('Search error:', error)
        return []
    }
}
