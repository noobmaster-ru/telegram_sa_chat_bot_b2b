import os
import asyncpg

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher

# create db connection pool and create tables in db
async def on_startup(
    dispatcher: Dispatcher,
    bot: Bot
) -> None:
    load_dotenv()
    POSTGRESQL_HOST = os.getenv("POSTGRESQL_HOST")
    POSTGRESQL_USER = os.getenv("POSTGRESQL_USER")
    POSTGRESQL_PASSWORD = os.getenv("POSTGRESQL_PASSWORD")
    POSTGRESQL_DBNAME = os.getenv("POSTGRESQL_DBNAME")

    # create pool connection to db and save it to workflow_data
    try:
        pool = await asyncpg.create_pool(
            host=POSTGRESQL_HOST,
            user=POSTGRESQL_USER,
            password=POSTGRESQL_PASSWORD,
            database=POSTGRESQL_DBNAME,
            min_size=1,  
            max_size=30  
        )
        dispatcher.workflow_data["db_pool"] = pool
        print("[INFO] PostgreSQL connection pool created successfully")

        # create table
        async with pool.acquire() as connection:
            table_exists = await connection.fetchval('''
                SELECT EXISTS (
                    SELECT FROM pg_tables
                    WHERE schemaname = 'public' AND tablename = 'users'
                );
            ''')
            if not table_exists:
                await connection.execute('''
                    CREATE TABLE IF NOT EXISTS users(
                        id serial PRIMARY KEY,
                        telegram_id BIGINT UNIQUE,
                        username TEXT,
                        wb_token TEXT,
                        table_url TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        last_update TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                print("[INFO] Create table users(id, telegram_id , username, wb_token, created_at)")

    except Exception as e:
        print(f"[ERROR] Error while creating PostgreSQL connection pool: {e}")
        await bot.session.close()
        exit(1)


# close pool connection to db
async def on_shutdown(dispatcher: Dispatcher):
    pool = dispatcher.workflow_data.get("db_pool")
    if pool:
        await pool.close()
        print("[INFO] PostgreSQL connection pool closed")
        