"""
Dynamic Database Tool Factory
مصنع الأدوات الديناميكي لقاعدة البيانات

This module automatically generates database tools from schema metadata.
Instead of manually writing tools for each table, we generate them dynamically.

هذا الوحدة تقوم بتوليد أدوات قاعدة البيانات تلقائياً من البيانات الوصفية.
بدلاً من كتابة أدوات يدوياً لكل جدول، نقوم بتوليدها ديناميكياً.
"""

from typing import Dict, Any, List, Callable, Optional, Type, Union
import logging
from datetime import datetime
import json
from functools import lru_cache

from .smart_finalizer import SmartFinalizerTool
from pydantic import create_model, Field, ValidationError, BaseModel

from ..config.schema_registry import (
    SCHEMA_METADATA,
    get_table_schema,
    get_required_columns,
    get_searchable_columns,
    has_vector_search,
    ColumnType
)
from ..config.database import get_supabase_client
from ..config.settings import settings

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# CACHED MODEL GENERATOR (Performance Optimization)
# -----------------------------------------------------------------------------
@lru_cache(maxsize=100)
def get_pydantic_model_cached(table_name: str, partial: bool = False) -> Type[BaseModel]:
    """
    Dynamically create a Pydantic model for validation.
    Cached to avoid recompiling the class on every request.
    """
    schema = SCHEMA_METADATA.get(table_name)
    if not schema:
        # Fallback empty model
        return create_model(f"Empty{table_name}Model")
        
    fields = {}
    
    for col in schema.get("columns", []):
        col_name = col["name"]
        
        # Skip auto-generated fields for inserts
        if not partial and col.get("auto_generated", False) and col_name not in ["id"]: 
            continue
            
        # Skip security fields (lawyer_id, user_id) if we handle them automatically
        if col.get("security_field", False):
            continue

        # Determine Python type
        py_type = str
        col_type = col.get("type")
        if col_type == ColumnType.INTEGER:
            py_type = int
        elif col_type == ColumnType.FLOAT:
            py_type = float
        elif col_type == ColumnType.BOOLEAN:
            py_type = bool
        elif col_type == ColumnType.JSON:
            py_type = Union[Dict[str, Any], List[Any]] # Explicit JSON structure
        elif col_type == ColumnType.ARRAY:
             py_type = List[str] # Default to List of strings for safety, or List[Any]
        elif col_type == ColumnType.VECTOR:
             py_type = List[float] # Vectors are explicitly list of floats
        
        # wrapper for Optional if partial or not required
        is_required = col.get("required", False) and not partial
        
        if is_required:
            fields[col_name] = (py_type, Field(..., description=col.get("description", "")))
        else:
            # ✅ FIX: Allow Filter Operators (gte, lte, etc) for query filters
            # If partial (used for filters), allow primitive OR dictionary (operator)
            if partial:
                fields[col_name] = (Optional[Union[py_type, Dict[str, Any]]], Field(None, description=col.get("description", "")))
            else:
                fields[col_name] = (Optional[py_type], Field(None, description=col.get("description", "")))
    
    model_name = f"{'Partial' if partial else 'New'}{table_name.title()}Model"
    return create_model(model_name, **fields)


class DatabaseToolGenerator:
    """
    Dynamic tool generator for database operations
    مولد الأدوات الديناميكي لعمليات قاعدة البيانات
    
    This class generates CRUD tools for each table defined in schema_registry
    """
    
    def __init__(self, lawyer_id: Optional[str] = None, current_user: Optional[Dict[str, Any]] = None):
        """
        Initialize tool generator
        
        Args:
            lawyer_id: ID of the lawyer (for security filtering)
            current_user: Context of the current user (for audit logging)
        """
        self.lawyer_id = lawyer_id
        self.current_user = current_user
        self.client = get_supabase_client()
        self.generated_tools: Dict[str, Callable] = {}
        
        # Generate all tools on init
        self._generate_all_tools()
        
        # Custom Gen 2 Tools
        self.smart_finalizer = SmartFinalizerTool()
        self.generated_tools["smart_finalize_task"] = self.smart_finalizer.run

        # Reduced logging to debug only to save IO logs
        logger.debug(f"✅ Generated {len(self.generated_tools)} dynamic database tools")

    # -------------------------------------------------------------------------
    # ENUM MAPPINGS (Arabic -> DB Values)
    # -------------------------------------------------------------------------
    STATUS_MAPPINGS = {
        "tasks": {
            "status": {
                "غير مكتملة": "pending", "معلقة": "pending", "جديدة": "pending",
                "جاري التنفيذ": "in_progress", "قيد التنفيذ": "in_progress", "قيد العمل": "in_progress",
                "مكتملة": "completed", "تمت": "completed", "منتهية": "completed",
                "ملغاة": "cancelled"
            },
            "priority": {
                "عالية": "high", "مرتفع": "high", "مهم": "high",
                "متوسطة": "medium", "عادي": "medium",
                "منخفضة": "low"
            }
        },
        "cases": {
            "status": {
                "نشطة": "active", "سارية": "active", "جارية": "active",
                "مغلقة": "closed", "منتهية": "closed", "محكوم فيها": "closed",
                "معلقة": "pending"
            }
        }
    }

    def _localize_enums(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate Arabic enum values to DB English constants.
        """
        mappings = self.STATUS_MAPPINGS.get(table_name, {})
        if not mappings:
            return data
            
        localized = data.copy()
        for field, value in data.items():
            if isinstance(value, str) and field in mappings:
                map_dict = mappings[field]
                # Try exact match or match ignoring whitespace
                clean_val = value.strip()
                if clean_val in map_dict:
                    localized[field] = map_dict[clean_val]
                    logger.info(f"🔄 Auto-translated {field}: '{value}' -> '{localized[field]}'")
        
        return localized

    # _create_pydantic_model removed in favor of module-level cached function

    # _log_to_audit removed - supersceded by DB Triggers
    # def _log_to_audit(...)


    def _compute_diff(self, old_data: Dict, new_updates: Dict) -> Dict[str, Any]:
        """Compute semantic difference between old and new values"""
        changes = {}
        for key, new_val in new_updates.items():
            old_val = old_data.get(key)
            # Simple string comparison to handle loose types (e.g. uuid vs string)
            if str(old_val) != str(new_val): 
                changes[key] = {
                    "old": old_val,
                    "new": new_val
                }
        return changes

    def _generate_all_tools(self):
        """Generate tools for all tables in schema registry (RESTRICTED)"""
        
        # 🚫 2. Blacklist System & Internal Tables
        BLACKLIST_TABLES = [
            "countries", "roles", "offices", "audit_logs", "users",
            "worksheets", "worksheet_sections", "legal_sources", "document_chunks", "thought_templates"
        ]
        
        for table_name, schema in SCHEMA_METADATA.items():
            if table_name in BLACKLIST_TABLES :
                logger.debug(f"🛑 Skipping blacklisted table: {table_name}")
                continue
            
            if schema.get("category", "") == "system":
                continue

            # ✅ 3. Only Generate INSERT & UPDATE (No Read/Delete)
            self._generate_insert_tool(table_name, schema)
            self._generate_update_tool(table_name, schema)
            
            # 3. Generate Query Tools (Read Access)
            self._generate_query_tool(table_name, schema)
            # self._generate_get_schema_tool(table_name, schema)
            
            # ✅ 4. Enable Delete Tools (User Authorized)
            self._generate_delete_tool(table_name, schema)
            
            # Log that vectors are pending if supported
            if schema.get("supports_vector_search", False):
                logger.debug(f"📋 Semantic search for {table_name} pending vector implementation")

        # ✅ 5. Custom Hybrid Tools (Surgical Operations)
        self._generate_safe_delete_client_tool()
    
    # =========================================================================
    # TOOL GENERATORS
    # =========================================================================
    
    def _generate_insert_tool(self, table_name: str, schema: Dict[str, Any]):
        """Generate INSERT tool for a table"""
        
        tool_name = f"insert_{table_name}"
        arabic_name = schema.get("arabic_name", table_name)
        required_cols = get_required_columns(table_name)
        
        
        
        # Generate Pydantic Model for Validation
        # Use cached global function
        InputModel = get_pydantic_model_cached(table_name, partial=False)

        def insert_function(**kwargs) -> Dict[str, Any]:
            """
            Dynamically generated INSERT function with Pydantic Validation
            """
            try:
                # ✅ 0.5 Localize Enums (Arabic -> English)
                # We do this on the raw kwargs before Pydantic validation
                localized_kwargs = self._localize_enums(table_name, kwargs)

                # 1. Pydantic Validation
                try:
                    validated_data = InputModel(**localized_kwargs).model_dump(exclude_unset=True)
                except ValidationError as ve:
                    return {
                        "success": False,
                        "error": f"Validation Error: {ve.errors()}",
                        "validation_details": ve.errors() # Friendly structured error
                    }

                # Security: Add lawyer_id if table is lawyer-filtered
                if schema.get("lawyer_filtered", False) and self.lawyer_id:
                    filter_col = schema.get("filter_column", "lawyer_id")
                    validated_data[filter_col] = self.lawyer_id
                
                # ---------------------------------------------------------------------
                # 🛑 ANTI-DUPLICATION PROTOCOL (Programmatic Enforcement)
                # ---------------------------------------------------------------------
                # Check for uniqueness before insertion to prevent duplicates
                # We check specific fields known to be unique or critical
                unique_checks = {
                    "national_id": "منطابق مع رقم الهوية",
                    "case_number": "منطابق مع رقم القضية",
                    "record_number": "منطابق مع رقم المحضر",
                    "email": "منطابق مع البريد الإلكتروني",
                    "phone": "منطابق مع رقم الهاتف"
                }

                check_query = self.client.table(table_name).select("*")
                has_check = False
                
                or_conditions = []
                for field_name, reason in unique_checks.items():
                    if validated_data.get(field_name):
                        or_conditions.append(f"{field_name}.eq.{validated_data[field_name]}")
                        has_check = True
                
                if has_check and or_conditions:
                    # Execute check
                    check_result = check_query.or_(",".join(or_conditions)).execute()
                    
                    if check_result.data and len(check_result.data) > 0:
                        existing_record = check_result.data[0]
                        match_reason = "سجل مشابه"
                        for field_name, reason in unique_checks.items():
                            if str(existing_record.get(field_name)) == str(validated_data.get(field_name)):
                                match_reason = reason
                                break
                        
                        logger.warning(f"🛑 Anti-Duplication Triggered: Found existing {table_name} ({match_reason})")
                        
                        return {
                            "success": False,
                            "error": f"⚠️ تكرار محتمل: وجدنا {arabic_name} موجود بالفعل ({match_reason})",
                            "existing_record": existing_record,
                            "recommendation": "يرجى استخدام السجل الموجود أو التعديل عليه بدلاً من إنشاء جديد."
                        }

                # ---------------------------------------------------------------------
                # Proceed with Insert
                # ---------------------------------------------------------------------

                # Add timestamps
                validated_data["created_at"] = datetime.now().isoformat()
                if "updated_at" in [c["name"] for c in schema.get("columns", [])]:
                    validated_data["updated_at"] = datetime.now().isoformat()
                
                # Insert into database
                result = self.client.table(table_name).insert(validated_data).execute()
                
                if result.data:
                    logger.info(f"✅ Inserted into {table_name}: {result.data[0].get('id', 'unknown')}")
                    
                    # Auto-Audit handled by DB Triggers
                    # self._log_to_audit("INSERT", table_name, result.data[0].get('id'), new_values=result.data[0], changes=validated_data)

                    
                    return {
                        "success": True,
                        "data": result.data[0],
                        "message": f"تم إضافة {arabic_name} بنجاح",
                        "inserted_id": result.data[0].get('id')
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to insert data"
                    }
                    
            except Exception as e:
                logger.error(f"❌ Insert failed for {table_name}: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }
        
        # Set function metadata for AI
        # Build detailed field descriptions
        fields_desc = []
        for col in schema.get("columns", []):
            c_name = col["name"]
            # Skip auto fields that AI shouldn't touch
            if col.get("auto_generated") and c_name != "id": continue
            if col.get("security_field"): continue # Skip hidden fields
            
            c_type = col.get("type", "string")
            if hasattr(c_type, "value"): c_type = c_type.value
            
            req_mark = "(Required)" if col.get("required") else "(Optional)"
            enum_vals = f" Allowed: {col['enum']}" if col.get("enum") else ""
            desc = col.get("description", "")
            
            fields_desc.append(f"- {c_name} ({c_type}) {req_mark}: {desc}{enum_vals}")

        fields_block = "\n        ".join(fields_desc)

        insert_function.__name__ = tool_name
        insert_function.__doc__ = f"""
        إضافة {arabic_name} جديد (Insert {table_name})
        
        {schema.get('description', '')}
        
        **Available Fields:**
        {fields_block}
        
        **Tips:**
        - Dates must be 'YYYY-MM-DD'.
        - Times must be 'HH:MM:SS'.
        - 'lawyer_id' is AUTOMATICALLY filled. Do not pass it.
        
        AI Instructions:
        {schema.get('ai_instructions', '')}
        """
        
        self.generated_tools[tool_name] = insert_function
    
    def _generate_query_tool(self, table_name: str, schema: Dict[str, Any]):
        """Generate QUERY/SEARCH tool for a table"""
        
        tool_name = f"query_{table_name}"
        arabic_name = schema.get("arabic_name", table_name)
        searchable_cols = get_searchable_columns(table_name)
        
        
        
        # Generate Filter Model
        # Use cached global function
        FilterModel = get_pydantic_model_cached(table_name, partial=True)

        def query_function(
            query: Optional[str] = None,
            filters: Optional[Any] = None, # can be dict or str (json)
            limit: int = 10,
            **kwargs # ✅ Swallow extra args like 'lawyer_id'
        ) -> Dict[str, Any]:
            """
            Dynamically generated QUERY function
            """
            try:
                # Handle filters if string (LLM quirk)
                if filters and isinstance(filters, str):
                    try:
                        filters = json.loads(filters)
                    except:
                        logger.warning(f"⚠️ Could not parse filters string: {filters}")
                        filters = {}

                # Start query builder
                db_query = self.client.table(table_name).select("*")
                
                # Security: Filter by lawyer_id
                if schema.get("lawyer_filtered", False) and self.lawyer_id:
                    filter_col = schema.get("filter_column", "lawyer_id")
                    db_query = db_query.eq(filter_col, self.lawyer_id)
                
                # Text search across searchable columns (Smart Filter)
                if query and searchable_cols:
                    active_search_cols = searchable_cols
                    
                    # 🧠 Smart Heuristic: Input Analysis
                    is_numeric = query.isdigit()
                    
                    if is_numeric:
                        # If numeric, prioritize ID fields (phone, national_id, id)
                        numeric_cols = [c for c in searchable_cols if "phone" in c or "id" in c or "number" in c]
                        if numeric_cols:
                            active_search_cols = numeric_cols
                            # If no specific numeric cols found, fallback to all (rare case)
                    else:
                        # If text (Arabic/English), Exclude purely numeric IDs to avoid false positives?
                        # Actually, keeping "phone" is bad for text search if phone is stored as string but content is alphanumeric.
                        # But typically we want to avoid searching "Ahmed" in "phone_number".
                        text_cols = [c for c in searchable_cols if "phone" not in c and "id" not in c and "number" not in c]
                        # Keep generic text fields like name, address, notes, email
                        if "full_name" in searchable_cols: text_cols.append("full_name") # Ensure name is always there
                        if "email" in searchable_cols: text_cols.append("email")
                        
                        # Deduplicate
                        active_search_cols = list(set(text_cols).intersection(set(searchable_cols)))
                        if not active_search_cols: active_search_cols = searchable_cols # Fallback

                    or_conditions = []
                    for col in active_search_cols:
                        or_conditions.append(f"{col}.ilike.%{query}%")
                    
                    if or_conditions:
                        db_query = db_query.or_(",".join(or_conditions))
                
                # Apply filters with Validation
                if filters and isinstance(filters, dict):
                    try:
                        # Validate filters against schema
                        # We use FilterModel to ensure fields exist and types are correct
                        # We allow extra fields in filters? No, strict is better.
                        validated_filters = FilterModel(**filters).model_dump(exclude_unset=True)
                        
                        for key, value in validated_filters.items():
                            db_query = db_query.eq(key, value)
                            
                    except ValidationError as ve:
                         logger.warning(f"⚠️ Invalid filters ignored for {table_name}: {ve}")
                         # We don't crash on query filters, just log and ignore invalid ones?
                         # Or we could return error. Let's return error to educate the agent.
                         return {
                             "success": False,
                             "error": f"Invalid filters: {ve.errors()}"
                         }
                
                # Limit results
                db_query = db_query.limit(limit)
                
                # Execute
                result = db_query.execute()
                
                return {
                    "success": True,
                    "data": result.data if result.data else [],
                    "count": len(result.data) if result.data else 0,
                    "message": f"تم العثور على {len(result.data) if result.data else 0} {arabic_name}"
                }
                
            except Exception as e:
                logger.error(f"❌ Query failed for {table_name}: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "data": []
                }
        
        query_function.__name__ = tool_name
        query_function.__doc__ = f"""
        البحث في {arabic_name} (Query {table_name})
        
        **Searchable Fields (Text):** {', '.join(searchable_cols) if searchable_cols else 'None'}
        
        **Args:**
        - query: Text to search in searchable fields.
        - filters: JSON dictionary for exact matches (e.g., {{"status": "pending"}}).
        - limit: Max results (default 10).
        
        **Common Filters:**
        - status: active, pending, closed
        - Date ranges: use 'gte', 'lte' logic if supported, otherwise filter in memory.
        
        AI Instructions:
        {schema.get('ai_instructions', '')}
        """
        
        self.generated_tools[tool_name] = query_function
    
    def _generate_get_schema_tool(self, table_name: str, schema: Dict[str, Any]):
        """Generate GET_SCHEMA tool - allows AI to inspect table structure"""
        
        tool_name = f"get_{table_name}_schema"
        arabic_name = schema.get("arabic_name", table_name)
        
        def get_schema_function() -> Dict[str, Any]:
            """
            Get schema information for this table
            """
            # Simplify column info for AI consumption
            columns_info = []
            for col in schema.get("columns", []):
                col_info = {
                    "name": col["name"],
                    "type": col["type"].value if isinstance(col["type"], ColumnType) else col["type"],
                    "description": col.get("description", ""),
                    "required": col.get("required", False)
                }
                
                if col.get("enum"):
                    col_info["allowed_values"] = col["enum"]
                if col.get("references"):
                    col_info["references_table"] = col["references"]
                    
                columns_info.append(col_info)
            
            return {
                "success": True,
                "table_name": table_name,
                "arabic_name": arabic_name,
                "description": schema.get("description", ""),
                "columns": columns_info,
                "required_fields": get_required_columns(table_name),
                "searchable_fields": get_searchable_columns(table_name),
                "supports_vector_search": schema.get("supports_vector_search", False),
                "ai_instructions": schema.get("ai_instructions", "")
            }
        
        get_schema_function.__name__ = tool_name
        get_schema_function.__doc__ = f"""
        عرض هيكل جدول {arabic_name}
        
        استخدم هذه الأداة عندما تحتاج لمعرفة:
        - ما هي الحقول المتاحة؟
        - ما هي الحقول الإجبارية؟
        - ما هي القيم المسموحة لحقل معين؟
        """
        
        self.generated_tools[tool_name] = get_schema_function
    
    def _generate_update_tool(self, table_name: str, schema: Dict[str, Any]):
        """Generate UPDATE tool for a table"""
        
        tool_name = f"update_{table_name}"
        arabic_name = schema.get("arabic_name", table_name)
        
        
        
        # Generate Partial Pydantic Model for Updates
        # Use cached global function
        UpdateModel = get_pydantic_model_cached(table_name, partial=True)

        def update_function(**kwargs) -> Dict[str, Any]:
            """
            Dynamically generated UPDATE function with Pydantic Validation
            """
            try:
                # 0. Extract ID & Updates from Flat Args
                # Agents tend to send flat JSON: {"id": "...", "status": "..."}
                # Instead of {"record_id": "...", "updates": {...}}
                
                record_id = kwargs.pop('id', None) or kwargs.pop('record_id', None)
                
                # If mapped from previous result with a specific name like 'case_id'
                if not record_id:
                     # Try to find any key ending in _id that matches table name approximately?
                     # Simpler: just look for common ID keys
                     target_id_key = f"{table_name}_id" # e.g. cases_id? No usually case_id
                     singular_name = table_name[:-1] if table_name.endswith('s') else table_name
                     target_id_key = f"{singular_name}_id"
                     record_id = kwargs.pop(target_id_key, None)

                if not record_id:
                    return {
                        "success": False,
                        "error": f"Missing ID for update. Please provide 'id' or '{arabic_name}_id'."
                    }
                
                updates = kwargs # Remaining args are updates
                
                # Handle updates if string (LLM quirk)
                if isinstance(updates, str):
                    try:
                        updates = json.loads(updates)
                    except:
                        return { "success": False, "error": f"Invalid JSON in updates: {updates}" }
                
                # ✅ 0.5 Localize Enums (Arabic -> English)
                updates = self._localize_enums(table_name, updates)

                # 1. Pydantic Validation
                try:
                    # Validate against schema (only fields present in updates)
                    validated_updates = UpdateModel(**updates).model_dump(exclude_unset=True)
                except ValidationError as ve:
                     return {
                        "success": False,
                        "error": f"Validation Error: {ve.errors()}",
                        "validation_details": ve.errors()
                    }

                # 2. Fetch OLD Data (for Audit)
                # We need this to compute diffs
                old_record_result = self.client.table(table_name).select("*").eq("id", record_id).execute()
                old_record = old_record_result.data[0] if old_record_result.data else None
                
                if not old_record:
                     return {
                        "success": False,
                        "error": f"{arabic_name} not found or permission denied"
                    }

                # Add updated_at timestamp
                validated_updates["updated_at"] = datetime.now().isoformat()
                
                # Build query
                db_query = self.client.table(table_name).update(validated_updates).eq("id", record_id)
                
                # Security: Filter by lawyer_id if applicable
                if schema.get("lawyer_filtered", False) and self.lawyer_id:
                    filter_col = schema.get("filter_column", "lawyer_id")
                    db_query = db_query.eq(filter_col, self.lawyer_id)
                
                result = db_query.execute()
                
                if result.data:
                    new_record = result.data[0]
                    logger.info(f"✅ Updated {table_name}: {record_id}")
                    
                    # Auto-Audit handled by DB Triggers
                    # self._log_to_audit("UPDATE", ...)

                    
                    return {
                        "success": True,
                        "data": new_record,
                        "message": f"تم تحديث {arabic_name} بنجاح",
                        "updated_id": record_id
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Update failed (DB returned no data)"
                    }
                    
            except Exception as e:
                logger.error(f"❌ Update failed for {table_name}: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }
        
        update_function.__name__ = tool_name
        update_function.__doc__ = f"""
        تحديث {arabic_name}
        
        Args:
            id (or {table_name[:-1]}_id): معرف السجل
            ...fields to update...
        """
        
        self.generated_tools[tool_name] = update_function
    
    def _generate_delete_tool(self, table_name: str, schema: Dict[str, Any]):
        """Generate DELETE tool for a table"""
        
        tool_name = f"delete_{table_name}"
        arabic_name = schema.get("arabic_name", table_name)
        
        def delete_function(confirm: bool = True, **kwargs) -> Dict[str, Any]:
            """
            Dynamically generated DELETE function
            """
            record_id = kwargs.pop('id', None) or kwargs.pop('record_id', None)
            
            if not record_id:
                 # Try singular id
                 singular_name = table_name[:-1] if table_name.endswith('s') else table_name
                 record_id = kwargs.pop(f"{singular_name}_id", None)
            
            if not record_id:
                return {
                    "success": False,
                    "error": "Missing ID for deletion."
                }

            if not confirm:
                # In Gen 2, we trust the agent more, but warn if explicit False.
                return {
                    "success": False,
                    "error": "⚠️ Deletion cancelled (confirm=False)."
                }
            
            try:
                # 2. Fetch OLD Data (for Audit)
                # This causes a GET request in logs, which is normal.
                old_record_result = self.client.table(table_name).select("*").eq("id", record_id).execute()
                old_record = old_record_result.data[0] if old_record_result.data else None
                
                # Build query
                # Explicitly requesting returned data to verify deletion
                # Force return=representation to ensure we get data back
                db_query = self.client.table(table_name).delete(count="exact").eq("id", record_id)
                
                # Security: Filter by lawyer_id if applicable
                current_lawyer_id = self.lawyer_id
                if schema.get("lawyer_filtered", False) and current_lawyer_id:
                    filter_col = schema.get("filter_column", "lawyer_id")
                    db_query = db_query.eq(filter_col, current_lawyer_id)
                    logger.info(f"🛡️ Applied Lawyer Filter: {filter_col}={current_lawyer_id}")
                else:
                    logger.warning(f"⚠️ No Lawyer Filter applied for {table_name} delete. (Admin Override?)")
                
                logger.info(f"🗑️ Executing PHYSICAL DELETE on {table_name} ID: {record_id}")
                result = db_query.execute()
                
                # Check execution
                deleted_rows = result.data if result.data else []
                deleted_count = len(deleted_rows)
                
                # Also check result.count if available
                if hasattr(result, "count") and result.count is not None:
                    deleted_count = result.count
                
                logger.info(f"📉 Delete Result: Count={deleted_count} | Data={deleted_rows}")

                if deleted_rows or deleted_count > 0:
                    logger.info(f"✅ Deleted from {table_name}: {record_id}")
                    
                    # Auto-Audit handled by DB Triggers
                    # if old_record: self._log_to_audit("DELETE", ...)

                    
                    return {
                        "success": True,
                        "deleted": True,
                        "message": f"تم حذف {arabic_name} بنجاح",
                        "deleted_id": record_id,
                        "details": f"Removed {deleted_count} records."
                    }
                else:
                    # If no data returned, it means ID didn't match (wrong ID or RLS hidden)
                    return {
                        "success": False,
                        "error": f"Delete failed: Record not found or permission denied.",
                        "details": f"ID {record_id} not found in {table_name} for this lawyer.",
                        "debug_lawyer_id": str(current_lawyer_id)
                    }
                    
            except Exception as e:
                logger.error(f"❌ Delete failed for {table_name}: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }
        
        delete_function.__name__ = tool_name
        delete_function.__doc__ = f"""
        حذف {arabic_name}
        
        Args:
            id: معرف السجل
            confirm: True (Default)
        """
        
        self.generated_tools[tool_name] = delete_function
    
    def _generate_vector_search_tool(self, table_name: str, schema: Dict[str, Any]):
        """Generate VECTOR SEARCH tool for tables with embeddings"""
        
        tool_name = f"semantic_search_{table_name}"
        arabic_name = schema.get("arabic_name", table_name)
        
        def vector_search_function(
            query: str,
            limit: int = 5,
            threshold: float = 0.7
        ) -> Dict[str, Any]:
            """
            Dynamically generated SEMANTIC SEARCH function
            """
            try:
                # 1. Generate Embedding
                from ..knowledge.embeddings import get_embedding
                query_embedding = get_embedding(query)
                
                if not query_embedding:
                     return {
                        "success": False,
                        "error": "Failed to generate embedding for query"
                    }

                # 2. Call RPC
                # Assuming a generic 'match_records' function exists in DB or using table-specific functions
                # For this dynamic tool, we'll assume a standard naming convention or a router RPC
                
                # Try specific function for the table first (e.g., match_cases, match_clients)
                rpc_name = f"match_{table_name}"
                
                params = {
                    "query_embedding": query_embedding,
                    "match_threshold": threshold,
                    "match_count": limit
                }
                
                # Add lawyer filtering to RPC params if needed
                if schema.get("lawyer_filtered", False) and self.lawyer_id:
                     params["filter_lawyer_id"] = self.lawyer_id

                # Execute RPC
                result = self.client.rpc(rpc_name, params).execute()
                
                return {
                    "success": True,
                    "data": result.data if result.data else [],
                    "message": f"Found {len(result.data) if result.data else 0} matches"
                }

            except Exception as e:
                logger.error(f"❌ Vector search failed for {table_name}: {e}")
                return {"success": False, "error": str(e)}

        vector_search_function.__name__ = tool_name
        self.generated_tools[tool_name] = vector_search_function

    def _generate_safe_delete_client_tool(self):
        """
        Generate SPECIALIZED safe delete tool for clients.
        Checks for dependencies (Cases, Tasks) before deleting.
        """
        tool_name = "safe_delete_client"
        
        def safe_delete_function(client_id: str, force: bool = False, reason: str = "") -> Dict[str, Any]:
            """
            Safely delete a client after checking for active cases/tasks.
            """
            try:
                # 1. Check for Active Cases
                cases_check = self.client.table("cases").select("id, status").eq("client_id", client_id).execute()
                active_cases = [c for c in cases_check.data if c.get("status") in ["active", "open", "in_progress"]]
                
                if active_cases and not force:
                    return {
                        "success": False,
                        "error": f"Cannot delete client: Found {len(active_cases)} active cases.",
                        "details": [case.get("id") for case in active_cases],
                        "recommendation": "Close these cases first or use force=True (requires valid reason)."
                    }

                # 2. Check for Pending Tasks
                tasks_check = self.client.table("tasks").select("id").eq("client_id", client_id).eq("status", "pending").execute()
                if tasks_check.data and not force:
                     return {
                        "success": False,
                        "error": f"Cannot delete client: Found {len(tasks_check.data)} pending tasks.",
                        "recommendation": "Complete/Cancel tasks first or use force=True."
                    }

                # 3. Proceed with Delete
                # We can reuse the dynamic delete logic or call DB directly
                # Let's call DB directly for simplicity
                result = self.client.table("clients").delete(count="exact").eq("id", client_id).execute()
                
                if result.count and result.count > 0:
                    logger.info(f"✅ Safe Delete Executed for Client {client_id}")
                    return {
                        "success": True, 
                        "message": "Client deleted successfully after safety checks.",
                        "deleted_id": client_id
                    }
                else:
                    return {
                        "success": False,
                        "error": "Delete failed: Client ID not found."
                    }

            except Exception as e:
                logger.error(f"❌ Safe Delete Failed: {e}")
                return {"success": False, "error": str(e)}

        safe_delete_function.__name__ = tool_name
        safe_delete_function.__doc__ = """
        حذف آمن للعميل (Safe Delete Client)
        
        Performs logic checks before deleting:
        1. Checks for active cases (Blocks delete if found).
        2. Checks for pending tasks (Blocks delete if found).
        
        Args:
            client_id: UUID
            force: Skip checks (Dangerous, requires reason)
            reason: Why forcing?
        """
        
        self.generated_tools[tool_name] = safe_delete_function

    # =========================================================================
    # PUBLIC API
    # =========================================================================
    
    def get_all_tools(self) -> Dict[str, Callable]:
        """
        Get all generated tools
        
        Returns:
            Dictionary of {tool_name: function}
        """
        return self.generated_tools
    
    def get_tool(self, tool_name: str) -> Optional[Callable]:
        """
        Get a specific tool by name
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool function or None
        """
        return self.generated_tools.get(tool_name)
    
    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """
        Get tool definitions in OpenAI function calling format
        
        Returns:
            List of tool definitions
        """
        tools = []
        
        for tool_name, func in self.generated_tools.items():
            # Parse function signature and docstring
            tool_def = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": func.__doc__ or f"Auto-generated tool: {tool_name}",
                    "parameters": self._generate_parameters_schema(tool_name, func)
                }
            }
            tools.append(tool_def)
        
        return tools
    
    def _generate_parameters_schema(self, tool_name: str, func: Callable) -> Dict[str, Any]:
        """Generate JSON schema for function parameters"""
        
        # Extract table name from tool name
        parts = tool_name.split("_")
        action = parts[0]  # insert, query, update, etc.
        table_name = "_".join(parts[1:])
        
        schema = get_table_schema(table_name)
        if not schema:
            return {"type": "object", "properties": {}}
        
        # Generate schema based on action type
        if action == "insert":
            return self._insert_params_schema(table_name, schema)
        elif action == "query":
            return self._query_params_schema(table_name, schema)
        elif action == "update":
            return self._update_params_schema(table_name, schema)
        elif action == "delete":
            return self._delete_params_schema(table_name, schema)
        elif action == "get" and "schema" in tool_name:
            return {"type": "object", "properties": {}}
        elif action == "semantic":
            return self._search_params_schema(table_name, schema)
        else:
            return {"type": "object", "properties": {}}
    
    def _insert_params_schema(self, table_name: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate parameters schema for INSERT operations"""
        properties = {}
        required = []
        
        for col in schema.get("columns", []):
            if col.get("auto_generated", False):
                continue
            if col.get("security_field", False):
                continue  # lawyer_id is added automatically
            
            col_name = col["name"]
            col_type = col.get("type")
            
            prop = {
                "description": col.get("description", "")
            }
            
            # Map column type to JSON schema type
            if col_type == ColumnType.STRING or col_type == ColumnType.TEXT:
                prop["type"] = "string"
            elif col_type == ColumnType.INTEGER:
                prop["type"] = "integer"
            elif col_type == ColumnType.FLOAT:
                prop["type"] = "number"
            elif col_type == ColumnType.BOOLEAN:
                prop["type"] = "boolean"
            elif col_type == ColumnType.UUID:
                prop["type"] = "string"
            elif col_type == ColumnType.DATE or col_type == ColumnType.DATETIME:
                prop["type"] = "string"
            else:
                prop["type"] = "string"
            
            # Add enum if available
            if col.get("enum"):
                prop["enum"] = col["enum"]
            
            properties[col_name] = prop
            
            if col.get("required", False):
                required.append(col_name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
    def _query_params_schema(self, table_name: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate parameters schema for QUERY operations"""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "نص للبحث في الحقول القابلة للبحث"
                },
                "filters": {
                    "type": "object",
                    "description": "فلاتر إضافية (مثل: {\"status\": \"active\"})"
                },
                "limit": {
                    "type": "integer",
                    "description": "عدد النتائج",
                    "default": 10
                }
            }
        }
    
    def _update_params_schema(self, table_name: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate parameters schema for UPDATE operations"""
        return {
            "type": "object",
            "properties": {
                "record_id": {
                    "type": "string",
                    "description": "معرف السجل المراد تحديثه"
                },
                "updates": {
                    "type": "object",
                    "description": "الحقول المراد تحديثها"
                }
            },
            "required": ["record_id", "updates"]
        }
    
    def _delete_params_schema(self, table_name: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate parameters schema for DELETE operations"""
        return {
            "type": "object",
            "properties": {
                "record_id": {
                    "type": "string",
                    "description": "معرف السجل المراد حذفه"
                },
                "confirm": {
                    "type": "boolean",
                    "description": "تأكيد الحذف (يجب أن يكون true)",
                    "default": False
                }
            },
            "required": ["record_id", "confirm"]
        }
    
    def _search_params_schema(self, table_name: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate parameters schema for SEMANTIC SEARCH"""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "سؤال أو نص للبحث الدلالي"
                },
                "limit": {
                    "type": "integer",
                    "description": "عدد النتائج",
                    "default": 5
                },
                "threshold": {
                    "type": "number",
                    "description": "الحد الأدنى للتشابه (0-1)",
                    "default": 0.7
                }
            },
            "required": ["query"]
        }

__all__ = ["DatabaseToolGenerator"]
