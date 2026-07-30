import asyncio
import asyncpg

async def reset_password():
    try:
        conn = await asyncpg.connect(user='postgres', password='postgres', database='postgres', host='127.0.0.1')
        print("Connected as postgres")
        try:
            await conn.execute("CREATE USER eln_user WITH PASSWORD 'eln_password';")
            print("User eln_user created")
        except asyncpg.exceptions.DuplicateObjectError:
            await conn.execute("ALTER USER eln_user WITH PASSWORD 'eln_password';")
            print("Password reset successful")
            
        try:
            # Terminate other connections before dropping the database
            await conn.execute("""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = 'eln_db'
                  AND pid <> pg_backend_pid();
            """)
            await conn.execute("DROP DATABASE IF EXISTS eln_db;")
            print("Dropped database eln_db")
        except Exception as e:
            print(f"Could not drop db: {e}")

        try:
            await conn.execute("CREATE DATABASE eln_db OWNER eln_user;")
            print("Database eln_db created")
        except asyncpg.exceptions.DuplicateDatabaseError:
            print("Database eln_db already exists")
            
        await conn.execute("GRANT ALL PRIVILEGES ON DATABASE eln_db TO eln_user;")
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(reset_password())
