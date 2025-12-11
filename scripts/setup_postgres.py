#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PostgreSQL Database Setup Script for Coal LIMS

This script creates the database and user for Coal LIMS.
Run this script before running Flask migrations.

Usage:
    python scripts/setup_postgres.py
"""

import sys

try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)


# Configuration
POSTGRES_HOST = 'localhost'
POSTGRES_PORT = 5432
POSTGRES_SUPERUSER = 'postgres'
POSTGRES_SUPERUSER_PASSWORD = '201320'  # Change this to your postgres password

# New database and user settings
DB_NAME = 'coal_lims'
DB_USER = 'coal_lims_user'
DB_PASSWORD = 'coal_lims_2025'


def create_database():
    """Create the database and user for Coal LIMS."""

    print(f"Connecting to PostgreSQL as {POSTGRES_SUPERUSER}...")

    try:
        # Connect to default postgres database
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database='postgres',
            user=POSTGRES_SUPERUSER,
            password=POSTGRES_SUPERUSER_PASSWORD
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        print("Connected successfully!")

        # Check if user exists
        cursor.execute(
            "SELECT 1 FROM pg_roles WHERE rolname = %s",
            (DB_USER,)
        )
        if not cursor.fetchone():
            print(f"Creating user '{DB_USER}'...")
            cursor.execute(
                sql.SQL("CREATE USER {} WITH PASSWORD %s").format(
                    sql.Identifier(DB_USER)
                ),
                (DB_PASSWORD,)
            )
            print(f"User '{DB_USER}' created.")
        else:
            print(f"User '{DB_USER}' already exists.")

        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (DB_NAME,)
        )
        if not cursor.fetchone():
            print(f"Creating database '{DB_NAME}'...")
            cursor.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(DB_NAME),
                    sql.Identifier(DB_USER)
                )
            )
            print(f"Database '{DB_NAME}' created.")
        else:
            print(f"Database '{DB_NAME}' already exists.")

        # Grant privileges
        print("Granting privileges...")
        cursor.execute(
            sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
                sql.Identifier(DB_NAME),
                sql.Identifier(DB_USER)
            )
        )

        cursor.close()
        conn.close()

        # Connect to the new database to set up schema permissions
        print(f"Connecting to '{DB_NAME}' to set up schema permissions...")
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=DB_NAME,
            user=POSTGRES_SUPERUSER,
            password=POSTGRES_SUPERUSER_PASSWORD
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Grant schema permissions
        cursor.execute(f"GRANT ALL ON SCHEMA public TO {DB_USER}")
        cursor.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {DB_USER}")
        cursor.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {DB_USER}")

        cursor.close()
        conn.close()

        print("\n" + "="*60)
        print("PostgreSQL Setup Complete!")
        print("="*60)
        print(f"\nDatabase URL for .env file:")
        print(f"DATABASE_URL=postgresql://{DB_USER}:{DB_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{DB_NAME}")
        print("\nNext steps:")
        print("1. Copy the DATABASE_URL above to your .env file")
        print("2. Run: flask db upgrade")
        print("3. Test the application")
        print("="*60)

        return True

    except psycopg2.Error as e:
        print(f"\nERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check if the password is correct")
        print("3. Check if port 5432 is accessible")
        return False


if __name__ == '__main__':
    success = create_database()
    sys.exit(0 if success else 1)
