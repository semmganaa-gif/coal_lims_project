"""Mine2NEMO connection diagnostics.

Mine2NEMO SQL Server-руу holбогдох алхамыг шалгаж, эхний алдааг тогтооно.

Хэрэглээ:
    python scripts/diagnose_mine2nemo.py

Алхам:
    1. Network ping (172.16.228.56)
    2. TCP port reachable (6964)
    3. pymssql package OK
    4. Connect to Mine2NEMO DB (sa)
    5. Connect to Lab DB (sa)  — Zobo-той ижил
    6. List databases (хэдэн DB байгаа)
    7. Test SELECT from QualityPlantFeed
"""

import socket
import subprocess
import sys

HOST = "172.16.228.56"
PORT = 1433  # SQL Server default — Zobo connection string-аас port-гүй =>  default
USER = "sa"
PASSWORD = "P@ssw0rd"


def step(name):
    print(f"\n{'=' * 60}")
    print(f"  {name}")
    print('=' * 60)


def step1_ping():
    step("1. Network reachable? (ping)")
    try:
        result = subprocess.run(
            ["ping", "-n", "2", HOST],
            capture_output=True, text=True, timeout=10,
        )
        if "TTL=" in result.stdout or "reply" in result.stdout.lower():
            print(f"  [OK] {HOST} ping success")
            return True
        else:
            print(f"  [FAIL] {HOST} not reachable")
            print(result.stdout[:300])
            return False
    except Exception as e:
        print(f"  [ERR] ping failed: {e}")
        return False


def step2_port():
    step(f"2. TCP port {PORT} open?")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        result = s.connect_ex((HOST, PORT))
        s.close()
        if result == 0:
            print(f"  [OK] Port {PORT} accepting connections")
            return True
        else:
            print(f"  [FAIL] Port {PORT} closed or firewalled (errno {result})")
            return False
    except Exception as e:
        print(f"  [ERR] socket test failed: {e}")
        return False


def step3_pymssql():
    step("3. pymssql installed?")
    try:
        import pymssql
        print(f"  [OK] pymssql version: {pymssql.__version__}")
        return True
    except ImportError:
        print("  [FAIL] pymssql not installed. Run: pip install pymssql")
        return False


def step4_connect(db_name, tds_version=None):
    label = f"'{db_name}' database as {USER}" + (f" (TDS {tds_version})" if tds_version else "")
    step(f"4. Connect to {label}")
    import pymssql
    try:
        kw = dict(
            server=HOST, port=PORT, user=USER, password=PASSWORD,
            database=db_name, timeout=10, login_timeout=10,
        )
        if tds_version:
            kw['tds_version'] = tds_version
        conn = pymssql.connect(**kw)
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        print(f"  [OK] Connected to {db_name}")
        print(f"  Server version: {version[:120]}...")
        return True
    except Exception as e:
        print(f"  [FAIL] {db_name} connection: {type(e).__name__}: {str(e)[:200]}")
        return False


def step5_list_dbs():
    step("5. List all databases on server")
    import pymssql
    try:
        conn = pymssql.connect(
            server=HOST, port=PORT, user=USER, password=PASSWORD,
            database="master", timeout=10, login_timeout=10,
        )
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sys.databases ORDER BY name")
        dbs = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        print(f"  [OK] {len(dbs)} databases found:")
        for db in dbs:
            marker = "  <-- TARGET" if db == "Mine2NEMO" else ""
            print(f"    - {db}{marker}")
        return "Mine2NEMO" in dbs
    except Exception as e:
        print(f"  [FAIL] list databases: {type(e).__name__}: {e}")
        return False


def step6_select():
    step("6. SELECT TOP 1 from Mine2NEMO.ProcessControl.QualityPlantFeed")
    import pymssql
    try:
        conn = pymssql.connect(
            server=HOST, port=PORT, user=USER, password=PASSWORD,
            database="Mine2NEMO", timeout=10, login_timeout=10,
        )
        cursor = conn.cursor()
        cursor.execute(
            "SELECT TOP 1 SampleCode, Mt_ar, Mad, Aad, CreatedDate "
            "FROM Mine2NEMO.ProcessControl.QualityPlantFeed "
            "ORDER BY CreatedDate DESC"
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            print(f"  [OK] Latest row: {row}")
        else:
            print("  [OK] Table exists, but empty")
        return True
    except Exception as e:
        print(f"  [FAIL] SELECT: {type(e).__name__}: {e}")
        return False


def main():
    print(f"Mine2NEMO diagnostic — target: {HOST}:{PORT}")
    print(f"User: {USER}")

    ok = step1_ping()
    if not ok:
        print("\n=> Сүлжээ хүрэхгүй. VPN/firewall шалгана уу.")
        sys.exit(1)

    ok = step2_port()
    if not ok:
        print("\n=> Port closed. SQL Server TCP/IP, firewall шалгана уу.")
        sys.exit(1)

    ok = step3_pymssql()
    if not ok:
        sys.exit(1)

    has_mine2nemo = step5_list_dbs()
    if not has_mine2nemo:
        print("\n=> 'Mine2NEMO' database байхгүй. Жагсаалтаас зөв нэрийг олно уу.")
        # Try Lab DB instead
        step4_connect("Lab")
        sys.exit(1)

    ok = step4_connect("Mine2NEMO")
    if not ok:
        print("\n=> Login failed. sa user/password шалгана уу.")
        sys.exit(1)

    step6_select()
    print("\n[SUCCESS] All checks passed!")


if __name__ == "__main__":
    main()
