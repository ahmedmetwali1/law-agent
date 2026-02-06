"""
Cache Keys Manager
مركزية إدارة مفاتيح التخزين المؤقت
"""


class CacheKeys:
    """مفاتيح Cache المحددة مسبقاً"""
    
    # ===== Global/Public Data =====
    COUNTRIES = "app:public:countries"
    
    # ===== User Profile Data =====
    @staticmethod
    def user_profile(user_id: str) -> str:
        return f"user:{user_id}:profile"
    
    @staticmethod
    def user_stats(user_id: str) -> str:
        return f"user:{user_id}:stats"
    
    # ===== Lawyer Dashboard Data =====
    @staticmethod
    def lawyer_dashboard_stats(lawyer_id: str) -> str:
        return f"lawyer:{lawyer_id}:dashboard:stats"
    
    @staticmethod
    def lawyer_recent_cases(lawyer_id: str, limit: int = 5) -> str:
        return f"lawyer:{lawyer_id}:dashboard:recent_cases:{limit}"
    
    @staticmethod
    def lawyer_upcoming_hearings(lawyer_id: str, limit: int = 5) -> str:
        return f"lawyer:{lawyer_id}:dashboard:hearings:{limit}"
    
    # ===== Lists Data =====
    @staticmethod
    def lawyer_cases(lawyer_id: str) -> str:
        return f"lawyer:{lawyer_id}:cases:list"
    
    @staticmethod
    def lawyer_tasks(lawyer_id: str, status: str = "all") -> str:
        return f"lawyer:{lawyer_id}:tasks:{status}"
    
    @staticmethod
    def lawyer_police_records(lawyer_id: str) -> str:
        return f"lawyer:{lawyer_id}:police_records"
    
    @staticmethod
    def lawyer_notifications(lawyer_id: str) -> str:
        return f"lawyer:{lawyer_id}:notifications"
    
    # ===== Case Details =====
    @staticmethod
    def case_details(case_id: str) -> str:
        return f"case:{case_id}:details"
    
    @staticmethod
    def case_opponents(case_id: str) -> str:
        return f"case:{case_id}:opponents"
    
    @staticmethod
    def case_hearings(case_id: str) -> str:
        return f"case:{case_id}:hearings"
    
    # ===== Invalidation Patterns =====
    @staticmethod
    def lawyer_all_data(lawyer_id: str) -> str:
        """نمط لحذف جميع بيانات محامي معين"""
        return f"lawyer:{lawyer_id}:*"
    
    @staticmethod
    def case_all_data(case_id: str) -> str:
        """نمط لحذف جميع بيانات قضية معينة"""
        return f"case:{case_id}:*"


# ===== TTL Constants (بالثواني) =====
class CacheTTL:
    """ثوابت مدد الصلاحية"""
    
    # Static/Rarely Changed Data
    COUNTRIES = 7 * 24 * 60 * 60  # 7 أيام
    USER_PROFILE = 30 * 60  # 30 دقيقة
    
    # Dashboard Data
    DASHBOARD_STATS = 2 * 60  # 2 دقيقة
    DASHBOARD_LISTS = 1 * 60  # 1 دقيقة
    
    # Account Stats
    ACCOUNT_STATS = 5 * 60  # 5 دقائق
    
    # Lists
    CASES_LIST = 3 * 60  # 3 دقائق
    TASKS_LIST = 30  # 30 ثانية
    POLICE_RECORDS = 5 * 60  # 5 دقائق
    NOTIFICATIONS = 30  # 30 ثانية
    
    # Case Details
    CASE_DETAILS = 5 * 60  # 5 دقائق
