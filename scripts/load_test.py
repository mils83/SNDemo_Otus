# -*- coding: utf-8 -*-
"""
Нагрузочный тест /user/search (ДЗ «Производительность индексов»).

Генератор имитирует реальный поиск: пары префиксов (имя, фамилия) разной
селективности выбираются случайно из реалистичного пула.

Пример запуска:
    python scripts/load_test.py --concurrency 100 --duration 15 --tag before
    python scripts/load_test.py --all --tag after
"""
import argparse
import asyncio
import csv
import os
import random
import string
import time
from statistics import mean

import httpx

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
LOGIN = "loadtest"
PASSWORD = "loadtest123"

# Пул пар (имя, фамилия): от частых селективностей к редким.
PREFIX_POOL = [
    ("Ан", "Ив"), ("Се", "См"), ("Дм", "Нов"), ("Ол", "Поп"), ("Мар", "Куз"),
    ("И", "Бе"), ("П", "Ма"), ("Ни", "Со"), ("Ек", "Мак"), ("Вл", "Тар"),
    ("Лю", "Бел"), ("Та", "Тит"), ("Ж", "Гу"), ("Ян", "Щ"), ("Кс", "Иг"),
    ("Экз", "Фы"), ("Ю", "Ц"), ("Щи", "Эь"), ("Ы", "Ъ"), ("Олив", "Попцо"),
]
LIMIT = 20


def percentile(sorted_samples: list, p: float) -> float:
    if not sorted_samples:
        return 0.0
    k = min(len(sorted_samples) - 1, int(len(sorted_samples) * p / 100))
    return sorted_samples[k]


def ensure_user(client: httpx.Client) -> str:
    """Логин от имени тестового пользователя (создаём, если нет)."""
    r = client.post(f"{BASE_URL}/login", data={"username": LOGIN, "password": PASSWORD})
    if r.status_code == 200:
        return r.json()["access_token"]
    r = client.post(f"{BASE_URL}/user/register", json={
        "username": LOGIN, "password": PASSWORD,
        "first_name": "Тест", "last_name": "Тестов", "birth_date": "1990-01-01",
        "gender": "male", "interests": "нагрузочное тестирование", "city": "Тестоград",
    })
    if r.status_code not in (201, 400):  # 400 = уже создан с другим паролем
        r.raise_for_status()
    r = client.post(f"{BASE_URL}/login", data={"username": LOGIN, "password": PASSWORD})
    r.raise_for_status()
    return r.json()["access_token"]


async def worker(client: httpx.AsyncClient, token: str,
                 stop_at: float, collect: list):
    """Воркер: шлёт поисковые запросы, пока не истечёт время замера."""
    rnd = random.Random()
    headers = {"Authorization": f"Bearer {token}"}
    while time.perf_counter() < stop_at:
        fp, lp = rnd.choice(PREFIX_POOL)
        t0 = time.perf_counter()
        try:
            r = await client.get(
                f"{BASE_URL}/user/search",
                params={"first_prefix": fp, "last_prefix": lp, "limit": LIMIT},
                headers=headers,
            )
            latency = (time.perf_counter() - t0) * 1000
            ok = (r.status_code == 200)
            if not ok:
                print(f"  ! HTTP {r.status_code}: {r.text[:120]}")
            collect.append((latency, ok))
        except Exception as e:
            latency = (time.perf_counter() - t0) * 1000
            collect.append((latency, False))
            print(f"  ! {type(e).__name__}: {e}")


async def run(concurrency: int, duration: float, warmup: float, token: str):
    limits = httpx.Limits(max_connections=concurrency + 10,
                          max_keepalive_connections=concurrency + 10)
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0), limits=limits) as client:
        collect = []
        await asyncio.gather(*[worker(client, token, time.perf_counter() + warmup, collect)
                               for _ in range(concurrency)])
        collect.clear()  # warmup не учитываем
        start = time.perf_counter()
        stop_at = start + duration
        await asyncio.gather(*[worker(client, token, stop_at, collect)
                               for _ in range(concurrency)])
        elapsed = time.perf_counter() - start
    return elapsed, collect


def summarize(tag, phase, concurrency, duration, elapsed, collect):
    lat = [(t) for t, ok in collect if ok]
    errors = sum(1 for _, ok in collect if not ok)
    lat.sort()
    rps = len(collect) / elapsed
    row = {
        "scenario": tag + "_" + phase,
        "phase": phase,  # before | after
        "concurrency": concurrency,
        "duration_s": round(elapsed, 1),
        "requests": len(collect),
        "errors": errors,
        "rps": round(rps, 1),
        "avg_ms": round(mean(lat), 1) if lat else 0,
        "p50_ms": round(percentile(lat, 50), 1) if lat else 0,
        "p95_ms": round(percentile(lat, 95), 1) if lat else 0,
        "p99_ms": round(percentile(lat, 99), 1) if lat else 0,
        "max_ms": round(lat[-1], 1) if lat else 0,
    }
    print(f"  [{row['scenario']}] req={len(collect)} err={errors} "
          f"rps={row['rps']} avg={row['avg_ms']} p95={row['p95_ms']} "
          f"p99={row['p99_ms']} max={row['max_ms']}")
    return row


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--concurrency", type=int)
    ap.add_argument("--duration", type=float, default=15.0)
    ap.add_argument("--warmup", type=float, default=5.0)
    ap.add_argument("--tag", default="run")
    ap.add_argument("--phase", default="before", choices=["before", "after"])
    ap.add_argument("--all", action="store_true",
                    help="прогоны по всем уровням параллелизма 1/10/100/1000")
    ap.add_argument("--out", default=os.path.join(
        os.path.dirname(__file__), "..", "reports", "loadtest_results.csv"))
    args = ap.parse_args()

    levels = [1, 10, 100, 1000] if args.all else [args.concurrency]
    rows_all = []
    for level in levels:
        print(f"=== concurrency={level}, phase={args.phase} ===")
        with httpx.Client(timeout=30.0) as c:
            token = ensure_user(c)
        elapsed, collect = await run(level, args.duration, args.warmup, token)
        rows_all.append(summarize(args.tag, args.phase, level,
                                  args.duration, elapsed, collect))
        # пауза, чтобы искажения очередь не переносила на другой уровень
        await asyncio.sleep(3)

    header = list(rows_all[0].keys())
    new_file = not os.path.exists(args.out)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        if new_file:
            w.writeheader()
        for row in rows_all:
            w.writerow(row)
    print(f"Сохранено в {os.path.abspath(args.out)}")


if __name__ == "__main__":
    asyncio.run(main())
