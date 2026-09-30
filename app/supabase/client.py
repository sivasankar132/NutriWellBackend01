import uuid
from typing import Optional, Any, Dict, List
from fastapi import HTTPException, status
from supabase import create_client, Client
from app.core.config import settings

_supabase_admin_client: Optional[Client] = None

def get_supabase_client() -> Client:
    """
    Returns the singleton administrative Supabase client configured with the server-side SUPABASE_KEY.
    """
    global _supabase_admin_client
    if _supabase_admin_client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SUPABASE_URL and SUPABASE_KEY must be set in environment variables."
            )
        _supabase_admin_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _supabase_admin_client

def get_user_supabase_client(access_token: str) -> Client:
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_URL and SUPABASE_KEY must be set in environment variables."
        )
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    client.postgrest.auth(access_token)
    return client


class LocalPgQueryBuilder:
    def __init__(self, table_name: str):
        self.table_name = table_name
        self._action = "select"
        self._select_cols = "*"
        self._filters: List[tuple] = []
        self._order_by: Optional[tuple] = None
        self._limit_val: Optional[int] = None
        self._offset_val: Optional[int] = None
        self._single: bool = False
        self._payload: Any = None

    def _get_conn(self):
        try:
            import psycopg2
        except ImportError:
            raise RuntimeError("psycopg2 is not installed. Local PostgreSQL fallback is unavailable.")
        conn = psycopg2.connect(
            dbname="nutriwell",
            user="postgres",
            password="siva@database",
            host="localhost",
            port=5432
        )
        conn.autocommit = True
        return conn

    def select(self, cols="*", **kwargs):
        self._action = "select"
        self._select_cols = cols
        return self

    def insert(self, payload, **kwargs):
        self._action = "insert"
        self._payload = payload
        return self

    def update(self, payload, **kwargs):
        self._action = "update"
        self._payload = payload
        return self

    def delete(self, **kwargs):
        self._action = "delete"
        return self

    def eq(self, column: str, value: Any):
        self._filters.append((column, "=", value))
        return self

    def neq(self, column: str, value: Any):
        self._filters.append((column, "!=", value))
        return self

    def gt(self, column: str, value: Any):
        self._filters.append((column, ">", value))
        return self

    def gte(self, column: str, value: Any):
        self._filters.append((column, ">=", value))
        return self

    def lt(self, column: str, value: Any):
        self._filters.append((column, "<", value))
        return self

    def lte(self, column: str, value: Any):
        self._filters.append((column, "<=", value))
        return self

    def like(self, column: str, value: str):
        self._filters.append((column, "LIKE", value))
        return self

    def ilike(self, column: str, value: str):
        self._filters.append((column, "ILIKE", value))
        return self

    def in_(self, column: str, values: List[Any]):
        self._filters.append((column, "IN", tuple(values)))
        return self

    def is_(self, column: str, value: Any):
        self._filters.append((column, "IS", value))
        return self

    def order(self, column: str, desc: bool = False, **kwargs):
        self._order_by = (column, "DESC" if desc else "ASC")
        return self

    def limit(self, count: int, **kwargs):
        self._limit_val = count
        return self

    def range(self, start: int, end: int):
        self._offset_val = start
        self._limit_val = (end - start + 1)
        return self

    def single(self):
        self._single = True
        return self

    def maybe_single(self):
        self._single = True
        return self

    def _clean_row(self, row: dict) -> dict:
        if not isinstance(row, dict):
            return row
        import datetime as dt_mod
        cleaned = {}
        for k, v in row.items():
            if isinstance(v, (uuid.UUID, dt_mod.datetime, dt_mod.date)):
                cleaned[k] = str(v)
            elif isinstance(v, list):
                cleaned[k] = [self._clean_row(i) if isinstance(i, dict) else i for i in v]
            else:
                cleaned[k] = v
        return cleaned

    def execute(self):
        try:
            import psycopg2.extras
        except ImportError:
            raise RuntimeError("psycopg2 is not installed. Local PostgreSQL fallback is unavailable.")
        conn = self._get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            where_clauses = []
            params = []
            for col, op, val in self._filters:
                if op == "IN":
                    where_clauses.append(f"{col} IN %s")
                    params.append(val)
                elif op == "IS":
                    where_clauses.append(f"{col} IS %s")
                    params.append(val)
                else:
                    where_clauses.append(f"{col} {op} %s")
                    params.append(val)
            where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

            if self._action == "select":
                clean_cols = "*"
                if self._select_cols and "(" not in str(self._select_cols):
                    clean_cols = self._select_cols
                
                order_sql = f" ORDER BY {self._order_by[0]} {self._order_by[1]}" if self._order_by else ""
                limit_sql = f" LIMIT {self._limit_val}" if self._limit_val is not None else ""
                offset_sql = f" OFFSET {self._offset_val}" if self._offset_val is not None else ""
                
                sql = f"SELECT {clean_cols} FROM public.{self.table_name}{where_sql}{order_sql}{limit_sql}{offset_sql};"
                cur.execute(sql, params)
                raw_rows = [dict(r) for r in cur.fetchall()]

                if self.table_name == "meals" and "*" in str(self._select_cols):
                    for r in raw_rows:
                        meal_id = r.get("id")
                        cur.execute("SELECT * FROM public.meal_items WHERE meal_id = %s;", (meal_id,))
                        r["meal_items"] = [dict(item) for item in cur.fetchall()]

                rows = [self._clean_row(r) for r in raw_rows]
                data_res = rows[0] if (self._single and rows) else rows
                return type("Result", (), {"data": data_res})()

            elif self._action == "insert":
                payload_list = self._payload if isinstance(self._payload, list) else [self._payload]
                inserted_rows = []
                for item in payload_list:
                    d = dict(item)
                    if "id" not in d and self.table_name != "users":
                        d["id"] = str(uuid.uuid4())
                    
                    cols = list(d.keys())
                    vals = [d[c] for c in cols]
                    cols_sql = ", ".join(cols)
                    placeholders = ", ".join(["%s"] * len(vals))
                    
                    sql = f"INSERT INTO public.{self.table_name} ({cols_sql}) VALUES ({placeholders}) RETURNING *;"
                    cur.execute(sql, vals)
                    inserted_rows.append(self._clean_row(dict(cur.fetchone())))

                data_res = inserted_rows[0] if (self._single and inserted_rows) else inserted_rows
                return type("Result", (), {"data": data_res})()

            elif self._action == "update":
                d = dict(self._payload) if isinstance(self._payload, dict) else {}
                set_clauses = [f"{k} = %s" for k in d.keys()]
                vals = list(d.values()) + params
                set_sql = ", ".join(set_clauses)

                sql = f"UPDATE public.{self.table_name} SET {set_sql}{where_sql} RETURNING *;"
                cur.execute(sql, vals)
                updated_rows = [self._clean_row(dict(r)) for r in cur.fetchall()]
                data_res = updated_rows[0] if (self._single and updated_rows) else updated_rows
                return type("Result", (), {"data": data_res})()

            elif self._action == "delete":
                sql = f"DELETE FROM public.{self.table_name}{where_sql} RETURNING *;"
                cur.execute(sql, params)
                deleted_rows = [self._clean_row(dict(r)) for r in cur.fetchall()]
                data_res = deleted_rows[0] if (self._single and deleted_rows) else deleted_rows
                return type("Result", (), {"data": data_res})()

        finally:
            conn.close()


class ResilientTableQuery:
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.local_builder = LocalPgQueryBuilder(table_name)
        self.remote_builder = None
        self._remote_error: Optional[Exception] = None
        try:
            client = get_supabase_client()
            self.remote_builder = client.table(table_name)
        except Exception as e:
            self._remote_error = e
            self.remote_builder = None

    def select(self, *args, **kwargs):
        self.local_builder.select(*args, **kwargs)
        if self.remote_builder:
            try:
                self.remote_builder = self.remote_builder.select(*args, **kwargs)
            except Exception as e:
                self._remote_error = e
                self.remote_builder = None
        return self

    def insert(self, *args, **kwargs):
        self.local_builder.insert(*args, **kwargs)
        if self.remote_builder:
            try:
                self.remote_builder = self.remote_builder.insert(*args, **kwargs)
            except Exception as e:
                self._remote_error = e
                self.remote_builder = None
        return self

    def update(self, *args, **kwargs):
        self.local_builder.update(*args, **kwargs)
        if self.remote_builder:
            try:
                self.remote_builder = self.remote_builder.update(*args, **kwargs)
            except Exception as e:
                self._remote_error = e
                self.remote_builder = None
        return self

    def delete(self, *args, **kwargs):
        self.local_builder.delete(*args, **kwargs)
        if self.remote_builder:
            try:
                self.remote_builder = self.remote_builder.delete(*args, **kwargs)
            except Exception as e:
                self._remote_error = e
                self.remote_builder = None
        return self

    def eq(self, *args, **kwargs):
        self.local_builder.eq(*args, **kwargs)
        if self.remote_builder:
            try:
                self.remote_builder = self.remote_builder.eq(*args, **kwargs)
            except Exception as e:
                self._remote_error = e
                self.remote_builder = None
        return self

    def neq(self, *args, **kwargs):
        self.local_builder.neq(*args, **kwargs)
        if self.remote_builder:
            try:
                self.remote_builder = self.remote_builder.neq(*args, **kwargs)
            except Exception as e:
                self._remote_error = e
                self.remote_builder = None
        return self

    def gt(self, *args, **kwargs):
        self.local_builder.gt(*args, **kwargs)
        if self.remote_builder:
            try:
                self.remote_builder = self.remote_builder.gt(*args, **kwargs)
            except Exception as e:
                self._remote_error = e
                self.remote_builder = None
        return self

    def gte(self, *args, **kwargs):
        self.local_builder.gte(*args, **kwargs)
        if self.remote_builder:
            try:
                self.remote_builder = self.remote_builder.gte(*args, **kwargs)
            except Exception as e:
                self._remote_error = e
                self.remote_builder = None
        return self

    def lt(self, *args, **kwargs):
        self.local_builder.lt(*args, **kwargs)
        if self.remote_builder:
            try:
                self.remote_builder = self.remote_builder.lt(*args, **kwargs)
            except Exception as e:
                self._remote_error = e
                self.remote_builder = None
        return self

    def lte(self, *args, **kwargs):
        self.local_builder.lte(*args, **kwargs)
        if self.remote_builder:
            try:
                self.remote_builder = self.remote_builder.lte(*args, **kwargs)
            except Exception as e:
                self._remote_error = e
                self.remote_builder = None
        return self

    def like(self, *args, **kwargs):
        self.local_builder.like(*args, **kwargs)
        if self.remote_builder:
            try:
                self.remote_builder = self.remote_builder.like(*args, **kwargs)
            except Exception as e:
                self._remote_error = e
                self.remote_builder = None
        return self

    def ilike(self, *args, **kwargs):
        self.local_builder.ilike(*args, **kwargs)
        if self.remote_builder:
            try:
                self.remote_builder = self.remote_builder.ilike(*args, **kwargs)
            except Exception as e:
                self._remote_error = e
                self.remote_builder = None
        return self

    def in_(self, *args, **kwargs):
        self.local_builder.in_(*args, **kwargs)
        if self.remote_builder:
            try:
                self.remote_builder = self.remote_builder.in_(*args, **kwargs)
            except Exception as e:
                self._remote_error = e
                self.remote_builder = None
        return self

    def is_(self, *args, **kwargs):
        self.local_builder.is_(*args, **kwargs)
        if self.remote_builder:
            try:
                self.remote_builder = self.remote_builder.is_(*args, **kwargs)
            except Exception as e:
                self._remote_error = e
                self.remote_builder = None
        return self

    def order(self, *args, **kwargs):
        self.local_builder.order(*args, **kwargs)
        if self.remote_builder:
            try:
                self.remote_builder = self.remote_builder.order(*args, **kwargs)
            except Exception as e:
                self._remote_error = e
                self.remote_builder = None
        return self

    def limit(self, *args, **kwargs):
        self.local_builder.limit(*args, **kwargs)
        if self.remote_builder:
            try:
                self.remote_builder = self.remote_builder.limit(*args, **kwargs)
            except Exception as e:
                self._remote_error = e
                self.remote_builder = None
        return self

    def range(self, *args, **kwargs):
        self.local_builder.range(*args, **kwargs)
        if self.remote_builder:
            try:
                self.remote_builder = self.remote_builder.range(*args, **kwargs)
            except Exception as e:
                self._remote_error = e
                self.remote_builder = None
        return self

    def single(self, *args, **kwargs):
        self.local_builder.single()
        if self.remote_builder:
            try:
                self.remote_builder = self.remote_builder.single(*args, **kwargs)
            except Exception as e:
                self._remote_error = e
                self.remote_builder = None
        return self

    def maybe_single(self, *args, **kwargs):
        self.local_builder.maybe_single()
        if self.remote_builder:
            try:
                self.remote_builder = self.remote_builder.maybe_single(*args, **kwargs)
            except Exception as e:
                self._remote_error = e
                self.remote_builder = None
        return self

    def execute(self):
        remote_err = self._remote_error
        if self.remote_builder:
            try:
                res = self.remote_builder.execute()
                print(f"[DB_SOURCE: SUPABASE_PRIMARY] Table='{self.table_name}' Action='{self.local_builder._action}' Status=SUCCESS")
                return res
            except Exception as e:
                remote_err = e
                err_str = str(e)
                print(f"[DB_SOURCE: LOCAL_POSTGRES_FALLBACK_ATTEMPT] Table='{self.table_name}' Action='{self.local_builder._action}' Reason='{err_str[:120]}'")

        try:
            res = self.local_builder.execute()
            print(f"[DB_SOURCE: LOCAL_POSTGRES_FALLBACK] Table='{self.table_name}' Action='{self.local_builder._action}' Status=SUCCESS")
            return res
        except Exception as local_err:
            if remote_err:
                raise remote_err
            raise local_err


class DynamicSupabaseProxy:
    def table(self, table_name: str):
        return ResilientTableQuery(table_name)

    def __getattr__(self, name: str):
        client = get_supabase_client()
        return getattr(client, name)

supabase = DynamicSupabaseProxy()
