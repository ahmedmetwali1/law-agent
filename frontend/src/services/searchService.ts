import { supabase } from '../supabaseClient'

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
        const { data: cases } = await supabase
            .from('cases')
            .select('id, case_number, subject, court_name')
            .eq('lawyer_id', lawyerId)
            .or(`case_number.ilike.%${trimmedQuery}%,subject.ilike.%${trimmedQuery}%,court_name.ilike.%${trimmedQuery}%`)
            .limit(5)

        if (cases) {
            cases.forEach(c => {
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
        const { data: clients } = await supabase
            .from('clients')
            .select('id, full_name, phone, email')
            .eq('lawyer_id', lawyerId)
            .or(`full_name.ilike.%${trimmedQuery}%,phone.ilike.%${trimmedQuery}%,email.ilike.%${trimmedQuery}%`)
            .limit(5)

        if (clients) {
            clients.forEach(client => {
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

        // 3. Search Opponents - DISABLED (table may not exist)
        // const { data: opponents } = await supabase
        //     .from('opponents')
        //     .select('id, name, case_id')
        //     .ilike('name', `%${trimmedQuery}%`)
        //     .limit(5)

        // if (opponents) {
        //     opponents.forEach(opp => {
        //         results.push({
        //             type: 'opponent',
        //             id: opp.id,
        //             title: opp.name,
        //             subtitle: 'خصم',
        //             path: `/cases/${opp.case_id}`,
        //             icon: '👥'
        //         })
        //     })
        // }

        // 4. Search Authorizations - DISABLED (table may not exist)
        // const { data: authorizations } = await supabase
        //     .from('authorizations')
        //     .select('id, authorization_number, client:clients(full_name)')
        //     .eq('lawyer_id', lawyerId)
        //     .ilike('authorization_number', `%${trimmedQuery}%`)
        //     .limit(5)

        // if (authorizations) {
        //     authorizations.forEach(auth => {
        //         results.push({
        //             type: 'authorization',
        //             id: auth.id,
        //             title: `توكيل ${auth.authorization_number}`,
        //             subtitle: (auth.client as any)?.full_name || '',
        //             path: `/authorizations/${auth.id}`,
        //             icon: '📄'
        //         })
        //     })
        // }

        return results
    } catch (error) {
        console.error('Search error:', error)
        return []
    }
}
