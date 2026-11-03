# -*- coding: utf-8 -*-
"""Сохраняет EXPLAIN (ANALYZE, BUFFERS) поискового запроса в reports/.

    python scripts/explain_query.py before
    python scripts/explain_query.py after
"""
import os
import sys

import psycopg2

PHASE = sys.argv[1] if len(sys.argv) > 1 else "before"
QUERIES = [
    ("Ан", "Ив", "common"),
    ("Ы", "Ъ", "worst_case"),
]

out_path = os.path.join(os.path.dirname(__file__), "..", "reports",
                        f"explain_{PHASE}.txt")

conn = psycopg2.connect(host=os.getenv("DB_HOST", "192.168.1.152"),
                        dbname="social_network", user="postgres",
                        password="postgres")
cur = conn.cursor()

with open(out_path, "a", encoding="utf-8") as f:
    for fp, lp, name in QUERIES:
        cur.execute(
            "EXPLAIN (ANALYZE, BUFFERS) "
            "SELECT id, first_name, last_name, birth_date::text, gender, "
            "interests, city FROM users "
            "WHERE first_name LIKE %s AND last_name LIKE %s "
            "ORDER BY id LIMIT 20",
            (fp + "%", lp + "%"),
        )
        f.write(f"--- [{PHASE}] first LIKE '{fp}%' AND last LIKE '{lp}%' ({name}) ---\n")
        for row in cur.fetchall():
            f.write(row[0] + "\n")
        f.write("\n")
conn.close()
print("saved:", os.path.abspath(out_path))
