import asyncio
import os
import sys
from pathlib import Path

api_path = Path(__file__).resolve().parent.parent / "apps" / "api"
if str(api_path) not in sys.path:
    sys.path.insert(0, str(api_path))

from sqlalchemy import text
from app.core.database import AsyncSessionLocal


async def inspect_schema() -> None:
    async with AsyncSessionLocal() as session:
        # 1. Fetch tables
        tables_res = await session.execute(
            text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
            )
        )
        tables = [r[0] for r in tables_res.fetchall()]

        print("=== POSTGRESQL TABLES IN DATABASE ===")
        for t in tables:
            print(f"  - {t}")

        print("\n=== TABLE CONSTRAINTS (Primary Keys, Foreign Keys, Unique) ===")
        constraints_res = await session.execute(
            text(
                """
                SELECT table_name, constraint_name, constraint_type 
                FROM information_schema.table_constraints 
                WHERE table_schema = 'public' AND constraint_type IN ('PRIMARY KEY', 'FOREIGN KEY', 'UNIQUE')
                ORDER BY table_name, constraint_type, constraint_name
                """
            )
        )
        for row in constraints_res.fetchall():
            print(f"  {row[0]:<25} | {row[2]:<15} | {row[1]}")

        print("\n=== INDEXES ===")
        indexes_res = await session.execute(
            text(
                """
                SELECT tablename, indexname 
                FROM pg_indexes 
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
                """
            )
        )
        for row in indexes_res.fetchall():
            print(f"  {row[0]:<25} | {row[1]}")


if __name__ == "__main__":
    asyncio.run(inspect_schema())
