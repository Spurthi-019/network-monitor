# database/db.py
# All database logic lives here.
# Creates tables, inserts data, queries history.
# Uses Python's built-in sqlite3 — no pip install needed.

import sys
from pathlib import Path

# Add parent directory to path so imports work when run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
import os
import time
from logger_setup import get_logger

logger = get_logger(__name__)

# Path to the database file
# It will be created automatically if it doesn't exist
DB_PATH = os.path.join("database", "network_monitor.db")


# ── Connection helper ─────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    """
    Open and return a connection to the SQLite database.

    detect_types lets SQLite understand Python data types.
    row_factory makes rows behave like dictionaries
    so you can do row["host"] instead of row[0].
    """
    conn = sqlite3.connect(
        DB_PATH,
        detect_types=sqlite3.PARSE_DECLTYPES
    )
    # This single line makes all query results return
    # as dictionaries instead of plain tuples
    conn.row_factory = sqlite3.Row
    return conn


# ── Table creation ────────────────────────────────────────────

def create_tables():
    """
    Create all database tables if they don't exist yet.
    Safe to call multiple times — won't overwrite existing data.
    Called once at application startup.
    """
    conn = get_connection()

    try:
        cursor = conn.cursor()

        # ── devices table ─────────────────────────────────────
        # Stores the list of devices to monitor
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                host       TEXT    NOT NULL UNIQUE,
                port       INTEGER NOT NULL DEFAULT 80,
                label      TEXT,
                created_at TEXT    NOT NULL
            )
        """)

        # ── metrics table ─────────────────────────────────────
        # Stores every monitoring result — one row per check
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                host                 TEXT    NOT NULL,
                port                 INTEGER,
                latency_ms           REAL,
                packet_loss_percent  REAL,
                reachable            INTEGER,
                health               TEXT,
                message              TEXT,
                timestamp            TEXT    NOT NULL
            )
        """)

        # ── alerts table ──────────────────────────────────────
        # Stores every diagnostic alert generated
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                host            TEXT NOT NULL,
                severity        TEXT NOT NULL,
                rule_triggered  TEXT,
                detail          TEXT,
                recommendation  TEXT,
                latency_ms      REAL,
                packet_loss_percent REAL,
                timestamp       TEXT NOT NULL
            )
        """)

        conn.commit()
        logger.info("Database tables created / verified successfully")

    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise

    finally:
        # Always close the connection when done
        conn.close()


# ── Device CRUD operations ────────────────────────────────────
# CRUD = Create, Read, Update, Delete

def insert_device(host: str, port: int, label: str = None) -> bool:
    """
    Add a new device to the devices table.

    Returns True if inserted, False if already exists.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO devices (host, port, label, created_at)
            VALUES (?, ?, ?, ?)
        """, (host, port, label or host,
              time.strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        logger.info(f"Device inserted: {host}:{port}")
        return True

    except sqlite3.IntegrityError:
        # UNIQUE constraint failed — device already exists
        logger.warning(f"Device already exists: {host}")
        return False

    except Exception as e:
        logger.error(f"Error inserting device {host}: {e}")
        return False

    finally:
        conn.close()


def get_all_devices() -> list:
    """
    Fetch all devices from the database.
    Returns a list of dictionaries.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, host, port, label, created_at
            FROM devices
            ORDER BY created_at ASC
        """)
        # dict(row) converts sqlite3.Row to a plain dictionary
        rows = [dict(row) for row in cursor.fetchall()]
        return rows

    except Exception as e:
        logger.error(f"Error fetching devices: {e}")
        return []

    finally:
        conn.close()


def get_device_by_host(host: str) -> dict:
    """Fetch a single device by hostname."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, host, port, label, created_at
            FROM devices WHERE host = ?
        """, (host,))
        row = cursor.fetchone()
        return dict(row) if row else None

    except Exception as e:
        logger.error(f"Error fetching device {host}: {e}")
        return None

    finally:
        conn.close()


def delete_device(host: str) -> bool:
    """Delete a device from the database by hostname."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM devices WHERE host = ?", (host,))
        conn.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Device deleted: {host}")
        return deleted

    except Exception as e:
        logger.error(f"Error deleting device {host}: {e}")
        return False

    finally:
        conn.close()


# ── Metrics operations ────────────────────────────────────────

def insert_metric(report: dict) -> bool:
    """
    Save one monitoring result to the metrics table.

    Args:
        report: dictionary from check_connectivity()
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO metrics
                (host, port, latency_ms, packet_loss_percent,
                 reachable, health, message, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report.get("host"),
            report.get("port", 80),
            report.get("latency_ms"),
            report.get("packet_loss_percent"),
            1 if report.get("reachable") else 0,
            report.get("health"),
            report.get("message"),
            report.get("timestamp",
                       time.strftime("%Y-%m-%d %H:%M:%S")),
        ))
        conn.commit()
        return True

    except Exception as e:
        logger.error(f"Error inserting metric: {e}")
        return False

    finally:
        conn.close()


def insert_many_metrics(reports: list) -> int:
    """
    Save multiple monitoring results in one database transaction.
    Much faster than calling insert_metric() in a loop.

    Returns the number of rows inserted.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        rows = []
        for r in reports:
            rows.append((
                r.get("host"),
                r.get("port", 80),
                r.get("latency_ms"),
                r.get("packet_loss_percent"),
                1 if r.get("reachable") else 0,
                r.get("health"),
                r.get("message"),
                r.get("timestamp",
                      time.strftime("%Y-%m-%d %H:%M:%S")),
            ))

        cursor.executemany("""
            INSERT INTO metrics
                (host, port, latency_ms, packet_loss_percent,
                 reachable, health, message, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, rows)
        conn.commit()
        logger.info(f"Inserted {len(rows)} metrics into database")
        return len(rows)

    except Exception as e:
        logger.error(f"Error inserting metrics batch: {e}")
        return 0

    finally:
        conn.close()


def get_metrics_for_host(host: str, limit: int = 50) -> list:
    """
    Get the last N monitoring results for a specific host.

    Args:
        host  : hostname to filter by
        limit : max number of rows to return (default 50)
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT *
            FROM   metrics
            WHERE  host = ?
            ORDER  BY timestamp DESC
            LIMIT  ?
        """, (host, limit))
        return [dict(row) for row in cursor.fetchall()]

    except Exception as e:
        logger.error(f"Error fetching metrics for {host}: {e}")
        return []

    finally:
        conn.close()


def get_all_metrics(limit: int = 100) -> list:
    """Get the last N monitoring results across all hosts."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT *
            FROM   metrics
            ORDER  BY timestamp DESC
            LIMIT  ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    except Exception as e:
        logger.error(f"Error fetching all metrics: {e}")
        return []

    finally:
        conn.close()


def get_metrics_summary() -> list:
    """
    Get average latency and loss per host across all time.
    Useful for the dashboard.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                host,
                COUNT(*)                        AS total_checks,
                ROUND(AVG(latency_ms), 2)       AS avg_latency_ms,
                ROUND(AVG(packet_loss_percent), 2) AS avg_loss_percent,
                SUM(CASE WHEN reachable = 1
                    THEN 1 ELSE 0 END)          AS times_online,
                SUM(CASE WHEN reachable = 0
                    THEN 1 ELSE 0 END)          AS times_offline,
                MAX(timestamp)                  AS last_checked
            FROM  metrics
            GROUP BY host
            ORDER BY host ASC
        """)
        return [dict(row) for row in cursor.fetchall()]

    except Exception as e:
        logger.error(f"Error fetching metrics summary: {e}")
        return []

    finally:
        conn.close()


# ── Alert operations ──────────────────────────────────────────

def insert_alert(alert_dict: dict) -> bool:
    """Save a diagnostic alert to the alerts table."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alerts
                (host, severity, rule_triggered, detail,
                 recommendation, latency_ms,
                 packet_loss_percent, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert_dict.get("host"),
            alert_dict.get("severity"),
            alert_dict.get("rule_triggered"),
            alert_dict.get("detail"),
            alert_dict.get("recommendation"),
            alert_dict.get("latency_ms"),
            alert_dict.get("packet_loss_percent"),
            alert_dict.get("timestamp",
                           time.strftime("%Y-%m-%d %H:%M:%S")),
        ))
        conn.commit()
        return True

    except Exception as e:
        logger.error(f"Error inserting alert: {e}")
        return False

    finally:
        conn.close()


def insert_many_alerts(alerts: list) -> int:
    """Save multiple alerts in one transaction."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        rows = [(
            a.get("host"),
            a.get("severity"),
            a.get("rule_triggered"),
            a.get("detail"),
            a.get("recommendation"),
            a.get("latency_ms"),
            a.get("packet_loss_percent"),
            a.get("timestamp",
                  time.strftime("%Y-%m-%d %H:%M:%S")),
        ) for a in alerts]

        cursor.executemany("""
            INSERT INTO alerts
                (host, severity, rule_triggered, detail,
                 recommendation, latency_ms,
                 packet_loss_percent, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, rows)
        conn.commit()
        logger.info(f"Inserted {len(rows)} alerts into database")
        return len(rows)

    except Exception as e:
        logger.error(f"Error inserting alerts batch: {e}")
        return 0

    finally:
        conn.close()


def get_alerts(severity: str = None, limit: int = 50) -> list:
    """
    Fetch alerts, optionally filtered by severity.

    Args:
        severity : "OK", "WARNING", or "CRITICAL" (or None for all)
        limit    : max rows to return
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if severity:
            cursor.execute("""
                SELECT * FROM alerts
                WHERE  severity = ?
                ORDER  BY timestamp DESC
                LIMIT  ?
            """, (severity.upper(), limit))
        else:
            cursor.execute("""
                SELECT * FROM alerts
                ORDER  BY timestamp DESC
                LIMIT  ?
            """, (limit,))

        return [dict(row) for row in cursor.fetchall()]

    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        return []

    finally:
        conn.close()


# ── Test this file directly ───────────────────────────────────
if __name__ == "__main__":
    from logger_setup import setup_logging
    setup_logging()

    print("=" * 55)
    print("  Phase 7 — Database Test")
    print("=" * 55)

    # Step 1: Create tables
    print("\n  Step 1: Creating tables...")
    create_tables()
    print("  ✓ Tables created")

    # Step 2: Insert devices
    print("\n  Step 2: Inserting devices...")
    insert_device("google.com",  80, "Google")
    insert_device("github.com",  80, "GitHub")
    insert_device("8.8.8.8",     53, "Google DNS")
    insert_device("1.1.1.1",     53, "Cloudflare DNS")
    print("  ✓ Devices inserted")

    # Step 3: Read devices back
    print("\n  Step 3: Reading devices from database...")
    devices = get_all_devices()
    for d in devices:
        print(f"  → {d['host']}:{d['port']}  ({d['label']})")

    # Step 4: Insert a fake metric
    print("\n  Step 4: Inserting a test metric...")
    insert_metric({
        "host":                 "google.com",
        "port":                 80,
        "latency_ms":           23.4,
        "packet_loss_percent":  0.0,
        "reachable":            True,
        "health":               "excellent",
        "message":              "Device is performing perfectly",
        "timestamp":            time.strftime("%Y-%m-%d %H:%M:%S"),
    })
    print("  ✓ Metric inserted")

    # Step 5: Read metrics back
    print("\n  Step 5: Reading metrics from database...")
    metrics = get_metrics_for_host("google.com")
    for m in metrics:
        print(f"  → {m['host']} | {m['latency_ms']}ms | "
              f"{m['health']} | {m['timestamp']}")

    # Step 6: Summary
    print("\n  Step 6: Metrics summary across all hosts...")
    summary = get_metrics_summary()
    for s in summary:
        print(f"  → {s['host']} | "
              f"avg={s['avg_latency_ms']}ms | "
              f"checks={s['total_checks']}")

    print("\n  ✓ Database test complete!")
    print(f"  Check your file: database/network_monitor.db")
