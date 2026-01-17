import React, { createContext, useContext, useState, useEffect } from 'react';

interface RolePermissions {
    cases?: { read?: boolean; create?: boolean; update?: boolean; delete?: boolean }
    clients?: { read?: boolean; create?: boolean; update?: boolean; delete?: boolean }
    hearings?: { read?: boolean; create?: boolean; update?: boolean; delete?: boolean }
    tasks?: { read?: boolean; create?: boolean; update?: boolean; delete?: boolean }
    all?: { read?: boolean; create?: boolean; update?: boolean; delete?: boolean }
}

interface UserProfile {
    id: string
    email: string
    full_name: string
    phone_number: string | null // ✅ Renamed from phone to phone_number
    country_id: string
    role_id: string
    office_id: string | null
    specialization: string | null
    license_number: string | null
    bio: string | null
    is_active: boolean
    // Relations
    country?: {
        id: string
        name_ar: string
        code: string
        flag_emoji: string
    }
    role?: {
        id: string
        name: string
        name_ar: string
        permissions?: RolePermissions  // ✅ NEW: الصلاحيات
    }
}

interface AuthContextType {
    user: UserProfile | null;
    profile: UserProfile | null;
    loading: boolean;
    isAdmin: boolean;
    isLawyer: boolean;  // ✅ NEW
    isAssistant: boolean;  // ✅ NEW
    officeId: string | null;  // ✅ NEW: المكتب الذي ينتمي له المستخدم
    signOut: () => Promise<void>;
    refreshProfile: () => Promise<void>;
    canPerform: (resource: string, action: string) => boolean;  // ✅ NEW
    getEffectiveLawyerId: () => string | null;  // ✅ NEW: للاستعلامات
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<UserProfile | null>(null);
    const [loading, setLoading] = useState(true);

    const fetchUserProfile = async (token: string) => {
        try {
            const response = await fetch('http://localhost:8000/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            })

            if (!response.ok) {
                throw new Error('Failed to fetch profile')
            }

            const data = await response.json()

            // ✅ Map DB columns to Frontend Interface
            const mappedUser: UserProfile = {
                ...data,
                phone_number: data.phone || null, // Map phone -> phone_number
            }

            setUser(mappedUser)
            setLoading(false)
        } catch (error) {
            console.error('Error fetching user profile:', error)
            // Clear invalid token
            localStorage.removeItem('access_token')
            localStorage.removeItem('user')
            setUser(null)
            setLoading(false)
        }
    }

    useEffect(() => {
        // Check for token on mount
        const token = localStorage.getItem('access_token')

        if (token) {
            fetchUserProfile(token)
        } else {
            setLoading(false)
        }
    }, [])

    const signOut = async () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')
        setUser(null)
        // Optionally call backend logout
        try {
            const token = localStorage.getItem('access_token')
            if (token) {
                await fetch('http://localhost:8000/api/auth/logout', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                })
            }
        } catch (error) {
            console.error('Logout error:', error)
        }
    };

    const refreshProfile = async () => {
        const token = localStorage.getItem('access_token')
        if (token) {
            await fetchUserProfile(token)
        }
    };

    // ✅ NEW: Helper function للتحقق من الصلاحيات
    const canPerform = (resource: string, action: string): boolean => {
        if (!user?.role?.permissions) return false

        // تحقق من صلاحية المورد المحدد أولاً
        const resourcePerms = user.role.permissions[resource as keyof RolePermissions]
        if (resourcePerms && typeof resourcePerms === 'object') {
            const actionPerm = resourcePerms[action as keyof typeof resourcePerms]
            if (actionPerm !== undefined) return actionPerm
        }

        // إذا لم يوجد، تحقق من صلاحية 'all'
        const allPerms = user.role.permissions.all
        if (allPerms && typeof allPerms === 'object') {
            const actionPerm = allPerms[action as keyof typeof allPerms]
            if (actionPerm !== undefined) return actionPerm
        }

        return false
    }

    // ✅ NEW: الحصول على الـ lawyer_id الفعال للاستعلامات
    const getEffectiveLawyerId = (): string | null => {
        if (!user) return null
        // إذا كان محامي → استخدم id الخاص به
        // إذا كان مساعد → استخدم office_id (المحامي الرئيسي)
        return user.office_id || user.id
    }

    const value: AuthContextType = {
        user,
        profile: user, // Alias for compatibility
        loading,
        isAdmin: user?.role?.name === 'admin',
        isLawyer: user?.role?.name === 'lawyer',  // ✅ NEW
        isAssistant: user?.role?.name === 'assistant',  // ✅ NEW
        officeId: user?.office_id || user?.id || null,  // ✅ NEW
        signOut,
        refreshProfile,
        canPerform,  // ✅ NEW
        getEffectiveLawyerId  // ✅ NEW
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
