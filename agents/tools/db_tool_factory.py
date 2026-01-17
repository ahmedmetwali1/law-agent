"""
Dynamic Database Tool Factory
مصنع الأدوات الديناميكي لقاعدة البيانات

This module automatically generates database tools from schema metadata.
Instead of manually writing tools for each table, we generate them dynamically.

هذا الوحدة تقوم بتوليد أدوات قاعدة البيانات تلقائياً من البيانات الوصفية.
بدلاً من كتابة أدوات يدوياً لكل جدول، نقوم بتوليدها ديناميكياً.
"""

from typing import Dict, Any, List, Callable, Optional
import logging
from datetime import datetime
import json

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
        
        logger.info(f"✅ Generated {len(self.generated_tools)} dynamic database tools")

    def _log_to_audit(self, action: str, table_name: str, record_id: str, changes: Dict[str, Any] = None, description: str = None):
        """
        Auto-log operation to audit_logs table
        """
        if table_name == 'audit_logs': return

        try:
            # Determine user info
            user_id = self.current_user.get('id') if self.current_user else self.lawyer_id
            user_name = self.current_user.get('full_name') if self.current_user else 'System'
            role = self.current_user.get('role', 'unknown') if self.current_user else 'system'
            
            log_entry = {
                "action": action,
                "table_name": table_name,
                "record_id": record_id,
                "user_id": user_id,
                "user_name": user_name,
                "user_role": role,
                "lawyer_id": self.lawyer_id, # ✅ Fix: Include lawyer_id for RLS/Filtering
                "changes": changes,
            }

            # ------------------------------------------------------------------
            # ENHANCEMENT: Fetch friendly name for description
            # ------------------------------------------------------------------
            if not description:
                try:
                    # Determine which column holds the "name" based on table
                    name_col = None
                    if table_name == 'users': name_col = 'full_name'
                    elif table_name == 'clients': name_col = 'full_name'
                    elif table_name == 'cases': name_col = 'case_title'
                    elif table_name == 'tasks': name_col = 'title'
                    elif table_name == 'hearings': name_col = 'hearing_date'
                    
                    record_name = "Unknown"
                    
                    # If we can identify a name column, fetch the record
                    if name_col:
                        # Optimization: If this is an INSERT, we might have the name in 'changes'
                        if action == "INSERT" and changes and name_col in changes:
                            record_name = changes[name_col]
                        else:
                            # Otherwise query DB (lightweight single row fetch)
                            rec = self.client.table(table_name).select(name_col).eq("id", record_id).single().execute()
                            if rec.data:
                                record_name = rec.data.get(name_col, "Unknown")
                    
                    # Create formatted description
                    arabic_table = SCHEMA_METADATA.get(table_name, {}).get('arabic_name', table_name)
                    # Example: "تحديث قضية: قضية النزاع التجاري"
                    description = f"{action} {arabic_table}: {record_name}"
                    
                except Exception as lookup_error:
                    # Fallback if lookup fails
                    description = f"{action} on {table_name}"
            
            log_entry["description"] = description
            
            # Fire and forget (don't block main op if log fails)
            self.client.table('audit_logs').insert(log_entry).execute()
            logger.debug(f"📝 Audit log created for {action} on {table_name}")
            
        except Exception as e:
            logger.error(f"⚠️ Audit Log Failed: {e}")

    def _generate_all_tools(self):
        """Generate tools for all tables in schema registry"""
        for table_name, schema in SCHEMA_METADATA.items():
            # Skip system tables for auto-generation
            if schema.get("category").value == "system":
                logger.debug(f"⏭️ Skipping system table: {table_name}")
                continue
            
            # Generate standard tools
            if table_name != 'audit_logs':
                self._generate_insert_tool(table_name, schema)
                
            self._generate_query_tool(table_name, schema)
            self._generate_get_schema_tool(table_name, schema)
            
            if table_name != 'audit_logs':
                self._generate_update_tool(table_name, schema)
                self._generate_delete_tool(table_name, schema)
            
            # Generate vector search tool if supported
            if schema.get("supports_vector_search", False):
                self._generate_vector_search_tool(table_name, schema)
    
    # =========================================================================
    # TOOL GENERATORS
    # =========================================================================
    
    def _generate_insert_tool(self, table_name: str, schema: Dict[str, Any]):
        """Generate INSERT tool for a table"""
        
        tool_name = f"insert_{table_name}"
        arabic_name = schema.get("arabic_name", table_name)
        required_cols = get_required_columns(table_name)
        
        def insert_function(**kwargs) -> Dict[str, Any]:
            """
            Dynamically generated INSERT function
            """
            try:
                # Security: Add lawyer_id if table is lawyer-filtered
                if schema.get("lawyer_filtered", False) and self.lawyer_id:
                    filter_col = schema.get("filter_column", "lawyer_id")
                    kwargs[filter_col] = self.lawyer_id
                
                # Validation: Check required fields
                missing_fields = [
                    field for field in required_cols 
                    if field not in kwargs or kwargs[field] is None
                ]
                
                if missing_fields:
                    return {
                        "success": False,
                        "error": f"Missing required fields: {', '.join(missing_fields)}",
                        "required_fields": required_cols
                    }
                
                # Add timestamps
                kwargs["created_at"] = datetime.now().isoformat()
                kwargs["updated_at"] = datetime.now().isoformat()
                
                # Insert into database
                result = self.client.table(table_name).insert(kwargs).execute()
                
                if result.data:
                    logger.info(f"✅ Inserted into {table_name}: {result.data[0].get('id', 'unknown')}")
                    
                    # Auto-Audit
                    self._log_to_audit("INSERT", table_name, result.data[0].get('id'), changes=kwargs)
                    
                    return {
                        "success": True,
                        "data": result.data[0],
                        "message": f"تم إضافة {arabic_name} بنجاح"
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
        insert_function.__name__ = tool_name
        insert_function.__doc__ = f"""
إضافة {arabic_name} جديد

{schema.get('description', '')}

Required fields: {', '.join(required_cols)}

AI Instructions:
{schema.get('ai_instructions', 'No special instructions')}
        """
        
        self.generated_tools[tool_name] = insert_function
    
    def _generate_query_tool(self, table_name: str, schema: Dict[str, Any]):
        """Generate QUERY/SEARCH tool for a table"""
        
        tool_name = f"query_{table_name}"
        arabic_name = schema.get("arabic_name", table_name)
        searchable_cols = get_searchable_columns(table_name)
        
        def query_function(
            query: Optional[str] = None,
            filters: Optional[Dict[str, Any]] = None,
            limit: int = 10
        ) -> Dict[str, Any]:
            """
            Dynamically generated QUERY function
            """
            try:
                # Start query builder
                db_query = self.client.table(table_name).select("*")
                
                # Security: Filter by lawyer_id
                if schema.get("lawyer_filtered", False) and self.lawyer_id:
                    filter_col = schema.get("filter_column", "lawyer_id")
                    db_query = db_query.eq(filter_col, self.lawyer_id)
                
                # Text search across searchable columns
                if query and searchable_cols:
                    # Build OR condition for text search
                    or_conditions = []
                    for col in searchable_cols:
                        or_conditions.append(f"{col}.ilike.%{query}%")
                    
                    if or_conditions:
                        db_query = db_query.or_(",".join(or_conditions))
                
                # Apply filters
                if filters:
                    for key, value in filters.items():
                        db_query = db_query.eq(key, value)
                
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
البحث في {arabic_name}

Searchable fields: {', '.join(searchable_cols) if searchable_cols else 'None'}


Args:
    query: نص للبحث في الحقول القابلة للبحث
    filters: فلاتر إضافية (مثل: {{"status": "active"}})
    limit: عدد النتائج (افتراضي: 10)

AI Instructions:
{schema.get('ai_instructions', 'No special instructions')}
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
        
        def update_function(record_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
            """
            Dynamically generated UPDATE function
            """
            try:
                # Add updated_at timestamp
                updates["updated_at"] = datetime.now().isoformat()
                
                # Build query
                db_query = self.client.table(table_name).update(updates).eq("id", record_id)
                
                # Security: Filter by lawyer_id if applicable
                if schema.get("lawyer_filtered", False) and self.lawyer_id:
                    filter_col = schema.get("filter_column", "lawyer_id")
                    db_query = db_query.eq(filter_col, self.lawyer_id)
                
                result = db_query.execute()
                
                if result.data:
                    logger.info(f"✅ Updated {table_name}: {record_id}")
                    
                    # Auto-Audit
                    self._log_to_audit("UPDATE", table_name, record_id, changes=updates)
                    
                    return {
                        "success": True,
                        "data": result.data[0],
                        "message": f"تم تحديث {arabic_name} بنجاح"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"{arabic_name} not found or permission denied"
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
    record_id: معرف السجل المراد تحديثه
    updates: الحقول المراد تحديثها (مثل: {{"status": "completed"}})
        """
        
        self.generated_tools[tool_name] = update_function
    
    def _generate_delete_tool(self, table_name: str, schema: Dict[str, Any]):
        """Generate DELETE tool for a table"""
        
        tool_name = f"delete_{table_name}"
        arabic_name = schema.get("arabic_name", table_name)
        
        def delete_function(record_id: str, confirm: bool = False) -> Dict[str, Any]:
            """
            Dynamically generated DELETE function
            """
            if not confirm:
                return {
                    "success": False,
                    "error": "⚠️ Deletion requires confirmation. Set confirm=True",
                    "warning": f"هل أنت متأكد من حذف هذا {arabic_name}؟"
                }
            
            try:
                # Build query
                db_query = self.client.table(table_name).delete().eq("id", record_id)
                
                # Security: Filter by lawyer_id if applicable
                if schema.get("lawyer_filtered", False) and self.lawyer_id:
                    filter_col = schema.get("filter_column", "lawyer_id")
                    db_query = db_query.eq(filter_col, self.lawyer_id)
                
                result = db_query.execute()
                
                if result.data:
                    logger.info(f"✅ Deleted from {table_name}: {record_id}")
                    
                    # Auto-Audit
                    self._log_to_audit("DELETE", table_name, record_id)
                    
                    return {
                        "success": True,
                        "message": f"تم حذف {arabic_name} بنجاح"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"{arabic_name} not found or permission denied"
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

⚠️ هذه عملية لا يمكن التراجع عنها!

Args:
    record_id: معرف السجل المراد حذفه
    confirm: يجب أن يكون True للتأكيد
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
                # TODO: Implement vector search using Supabase RPC
                # This requires:
                # 1. Generate embedding for query
                # 2. Call match_documents RPC function
                # 3. Return results
                
                logger.warning(f"⚠️ Vector search not yet implemented for {table_name}")
                return {
                    "success": False,
                    "error": "Vector search feature coming soon",
                    "data": []
                }
                
            except Exception as e:
                logger.error(f"❌ Vector search failed for {table_name}: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "data": []
                }
        
        vector_search_function.__name__ = tool_name
        vector_search_function.__doc__ = f"""
البحث الدلالي في {arabic_name}

يستخدم الذكاء الاصطناعي للبحث بالمعنى وليس فقط بالنص.

Args:
    query: سؤال أو نص للبحث
    limit: عدد النتائج
    threshold: الحد الأدنى للتشابه (0-1)
        """
        
        self.generated_tools[tool_name] = vector_search_function
    
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
                prop["format"] = "uuid"
            elif col_type == ColumnType.DATE or col_type == ColumnType.DATETIME:
                prop["type"] = "string"
                prop["format"] = "date" if col_type == ColumnType.DATE else "date-time"
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
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a generated tool
        
        Args:
            tool_name: Name of the tool
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool not found: {tool_name}"
            }
        
        try:
            return tool(**kwargs)
        except Exception as e:
            logger.error(f"❌ Tool execution failed: {tool_name} - {e}")
            return {
                "success": False,
                "error": str(e)
            }


__all__ = ["DatabaseToolGenerator"]
