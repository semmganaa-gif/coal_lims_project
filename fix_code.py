# -*- coding: utf-8 -*-
"""
Бүх кодын засваруудыг хийх script
"""
import re

def fix_chat_api():
    """chat_api.py засах"""
    filepath = 'app/routes/api/chat_api.py'

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Import нэмэх
    content = content.replace(
        'from sqlalchemy import or_, and_, func\n\n\nALLOWED_EXTENSIONS',
        'from sqlalchemy import or_, and_, func\nfrom app.utils.security import escape_like_pattern\n\n\nALLOWED_EXTENSIONS'
    )

    # 2. search escape
    content = content.replace(
        "if search:\n            query = query.filter(ChatMessage.message.ilike(f'%{search}%'))",
        "if search:\n            safe_search = escape_like_pattern(search)\n            query = query.filter(ChatMessage.message.ilike(f'%{safe_search}%'))"
    )

    # 3. query_text escape
    content = content.replace(
        "q = ChatMessage.query.filter(\n            ChatMessage.message.ilike(f'%{query_text}%'),",
        "safe_query_text = escape_like_pattern(query_text)\n        q = ChatMessage.query.filter(\n            ChatMessage.message.ilike(f'%{safe_query_text}%'),"
    )

    # 4. samples search escape
    content = content.replace(
        "samples = Sample.query.filter(\n            or_(\n                Sample.sample_code.ilike(f'%{query}%'),\n                Sample.client_name.ilike(f'%{query}%'),\n                Sample.sample_type.ilike(f'%{query}%')",
        "safe_query = escape_like_pattern(query)\n        samples = Sample.query.filter(\n            or_(\n                Sample.sample_code.ilike(f'%{safe_query}%'),\n                Sample.client_name.ilike(f'%{safe_query}%'),\n                Sample.sample_type.ilike(f'%{safe_query}%')"
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ {filepath} засагдлаа")


def fix_equipment_routes():
    """equipment_routes.py - datetime.now() -> now_local()"""
    filepath = 'app/routes/equipment_routes.py'

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Import нэмэх
    if 'from app.utils.datetime import now_local' not in content:
        content = content.replace(
            'from datetime import datetime, timedelta',
            'from datetime import datetime, timedelta\nfrom app.utils.datetime import now_local'
        )

    # datetime.now() -> now_local()
    content = content.replace('datetime.now()', 'now_local()')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ {filepath} засагдлаа")


def fix_report_routes():
    """report_routes.py засах"""
    filepath = 'app/routes/report_routes.py'

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'from app.utils.datetime import now_local' not in content:
        content = content.replace(
            'from datetime import datetime',
            'from datetime import datetime\nfrom app.utils.datetime import now_local'
        )

    content = content.replace('datetime.now()', 'now_local()')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ {filepath} засагдлаа")


def fix_samples_api():
    """samples_api.py засах"""
    filepath = 'app/routes/api/samples_api.py'

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'from app.utils.datetime import now_local' not in content:
        content = content.replace(
            'from datetime import datetime',
            'from datetime import datetime\nfrom app.utils.datetime import now_local'
        )

    content = content.replace('datetime.now()', 'now_local()')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ {filepath} засагдлаа")


def fix_audit_api():
    """audit_api.py засах"""
    filepath = 'app/routes/api/audit_api.py'

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'from app.utils.datetime import now_local' not in content:
        content = content.replace(
            'from datetime import datetime',
            'from datetime import datetime\nfrom app.utils.datetime import now_local'
        )

    content = content.replace('datetime.now()', 'now_local()')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ {filepath} засагдлаа")


def fix_quality_helpers():
    """quality_helpers.py засах"""
    filepath = 'app/utils/quality_helpers.py'

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'from app.utils.datetime import now_local' not in content:
        content = content.replace(
            'from datetime import datetime',
            'from datetime import datetime\nfrom app.utils.datetime import now_local'
        )

    content = content.replace('datetime.now()', 'now_local()')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ {filepath} засагдлаа")


def fix_notifications():
    """notifications.py засах"""
    filepath = 'app/utils/notifications.py'

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'from app.utils.datetime import now_local' not in content:
        content = content.replace(
            'from datetime import datetime',
            'from datetime import datetime\nfrom app.utils.datetime import now_local'
        )

    content = content.replace('datetime.now()', 'now_local()')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ {filepath} засагдлаа")


def fix_monitoring():
    """monitoring.py - unused variables"""
    filepath = 'app/monitoring.py'

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace(
        'def __exit__(self, exc_type, exc_val, exc_tb):',
        'def __exit__(self, _exc_type, _exc_val, _exc_tb):'
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ {filepath} засагдлаа")


def main():
    print("=" * 50)
    print("Coal LIMS - Code Fixes")
    print("=" * 50)

    try:
        fix_chat_api()
    except Exception as e:
        print(f"❌ chat_api.py: {e}")

    try:
        fix_equipment_routes()
    except Exception as e:
        print(f"❌ equipment_routes.py: {e}")

    try:
        fix_report_routes()
    except Exception as e:
        print(f"❌ report_routes.py: {e}")

    try:
        fix_samples_api()
    except Exception as e:
        print(f"❌ samples_api.py: {e}")

    try:
        fix_audit_api()
    except Exception as e:
        print(f"❌ audit_api.py: {e}")

    try:
        fix_quality_helpers()
    except Exception as e:
        print(f"❌ quality_helpers.py: {e}")

    try:
        fix_notifications()
    except Exception as e:
        print(f"❌ notifications.py: {e}")

    try:
        fix_monitoring()
    except Exception as e:
        print(f"❌ monitoring.py: {e}")

    print("=" * 50)
    print("ДУУСЛАА!")
    print("=" * 50)


if __name__ == '__main__':
    main()
