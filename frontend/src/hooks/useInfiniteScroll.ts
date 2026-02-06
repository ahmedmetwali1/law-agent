import { useState, useEffect, useCallback, useRef } from 'react'
import { apiClient } from '../api/client'
import { toast } from 'sonner'

interface UseInfiniteScrollProps<T> {
    endpoint: string
    limit?: number
    initialParams?: Record<string, any>
    onError?: (error: any) => void
}

interface UseInfiniteScrollReturn<T> {
    data: T[]
    loading: boolean
    hasMore: boolean
    loadMore: () => void
    refresh: () => void
    setParams: (params: Record<string, any>) => void
    total: number
}

export function useInfiniteScroll<T>({
    endpoint,
    limit = 20,
    initialParams = {},
    onError
}: UseInfiniteScrollProps<T>): UseInfiniteScrollReturn<T> {
    const [data, setData] = useState<T[]>([])
    const [loading, setLoading] = useState(false)
    const [page, setPage] = useState(1)
    const [hasMore, setHasMore] = useState(true)
    const [total, setTotal] = useState(0)
    const [params, setParamsState] = useState(initialParams)

    // To prevent race conditions
    const loadingRef = useRef(false)
    const pageRef = useRef(1)

    const fetchData = useCallback(async (pageNum: number, currentParams: any, isRefresh = false) => {
        if (loadingRef.current) return

        loadingRef.current = true
        setLoading(true)

        try {
            const queryParams = new URLSearchParams()
            queryParams.append('page', pageNum.toString())
            queryParams.append('limit', limit.toString())

            // Add custom params (filters, search, etc.)
            Object.entries(currentParams).forEach(([key, value]) => {
                if (value !== undefined && value !== null && value !== '') {
                    queryParams.append(key, value.toString())
                }
            })

            const url = `${endpoint}?${queryParams.toString()}`
            const response: any = await apiClient.get(url)

            if (response && Array.isArray(response.data)) {
                // Determine if we have more data
                const newData = response.data
                const totalCount = response.total || 0

                setTotal(totalCount)

                if (isRefresh) {
                    setData(newData)
                } else {
                    setData(prev => [...prev, ...newData])
                }

                // If we got fewer items than limit, we've reached the end
                setHasMore(newData.length === limit)
            } else {
                setHasMore(false)
            }
        } catch (error) {
            console.error('Error fetching data:', error)
            if (onError) onError(error)
            else toast.error('فشل تحميل البيانات')
            setHasMore(false)
        } finally {
            setLoading(false)
            loadingRef.current = false
        }
    }, [endpoint, limit, onError])

    // Load next page
    const loadMore = useCallback(() => {
        if (!hasMore || loadingRef.current) return

        const nextPage = pageRef.current + 1
        pageRef.current = nextPage
        setPage(nextPage)

        fetchData(nextPage, params, false)
    }, [fetchData, hasMore, params])

    // Reset and reload (e.g., when search changes)
    const refresh = useCallback(() => {
        pageRef.current = 1
        setPage(1)
        setHasMore(true)
        setData([]) // Clear immediately for better UX on searching
        fetchData(1, params, true)
    }, [fetchData, params])

    // Update params and trigger refresh
    const setParams = useCallback((newParams: Record<string, any>) => {
        setParamsState(prev => {
            // Only update if actually changed to avoid loop
            if (JSON.stringify(prev) === JSON.stringify(newParams)) return prev
            return newParams
        })
    }, [])

    // Initial load and param changes
    useEffect(() => {
        refresh()
    }, [params]) // eslint-disable-line react-hooks/exhaustive-deps

    return {
        data,
        loading,
        hasMore,
        loadMore,
        refresh,
        setParams,
        total
    }
}
