"""
FraudGuard AI — Phase 2: Dataset Verification Script (Fast)
============================================================
Fast, memory-efficient verification of all raw datasets.

Strategy:
  - Use shell `wc -l` for row counts (fast on any file size)
  - Use pandas read_csv with usecols=[target] to count fraud labels
    without loading all 394+ columns into memory
  - Use pandas read_csv with nrows=0 to get column list
  - Load small files (<= 30 MB) fully to check duplicates
  - Never modifies raw data

Run with:
  venv/bin/python scripts/phase2_verify_datasets.py
"""

import os
import sys
import hashlib
import json
import subprocess
import time
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR   = REPO_ROOT / "data" / "raw"

DATASETS = {
    "PaySim": {
        "path": RAW_DIR / "PS_20174392719_1491204439457_log.csv",
        "target": "isFraud",
        "expected_rows": 6_362_620,
        "expected_cols": 11,
        "role": "PRIMARY",
        "check_dupes": False,   # too large
    },
    "ULB Credit Card": {
        "path": RAW_DIR / "creditcard.csv",
        "target": "Class",
        "expected_rows": 284_807,
        "expected_cols": 31,
        "role": "BENCHMARK",
        "check_dupes": True,
    },
    "UPI Fraud": {
        "path": RAW_DIR / "fraud_dataset.csv",
        "target": "is_fraud",
        "expected_rows": 26_393,
        "expected_cols": 65,
        "role": "REJECTED",
        "check_dupes": True,
    },
    "IEEE-CIS Transaction": {
        "path": RAW_DIR / "IEEE_CIS archive (3)" / "train_transaction.csv",
        "target": "isFraud",
        "expected_rows": 590_540,
        "expected_cols": 394,
        "role": "SECONDARY",
        "check_dupes": False,   # too large and wide
    },
    "IEEE-CIS Identity": {
        "path": RAW_DIR / "IEEE_CIS archive (3)" / "train_identity.csv",
        "target": None,
        "expected_rows": 144_233,
        "expected_cols": 41,
        "role": "SECONDARY (join file)",
        "check_dupes": False,
    },
}

SEP = "=" * 72


def wc_lines(path: Path) -> int:
    """Fast line count via wc -l (subtracts 1 for header)."""
    result = subprocess.run(
        ["wc", "-l", str(path)],
        capture_output=True, text=True
    )
    return int(result.stdout.strip().split()[0]) - 1   # minus header line


def sha256_prefix(path: Path, n_bytes: int = 65536) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read(n_bytes))
    return h.hexdigest()[:16]


def file_size_mb(path: Path) -> float:
    return round(path.stat().st_size / (1024 ** 2), 2)


def verify_dataset(name: str, cfg: dict) -> dict:
    path   = cfg["path"]
    target = cfg["target"]

    print(f"\n{SEP}")
    print(f"  {name}")
    print(f"  {path.name}")
    print(SEP)

    result = {
        "name": name,
        "role": cfg["role"],
        "file_path": str(path),
        "file_exists": path.exists(),
        "file_size_mb": None,
        "sha256_prefix": None,
        "total_rows": None,
        "num_columns": None,
        "columns": None,
        "target_col": target,
        "target_found": None,
        "fraud_count": None,
        "legit_count": None,
        "fraud_pct": None,
        "missing_values": None,
        "duplicate_rows": None,
        "row_count_ok": None,
        "col_count_ok": None,
        "status": None,
        "errors": [],
    }

    if not path.exists():
        msg = f"FILE NOT FOUND: {path}"
        print(f"  ❌ {msg}")
        result["status"] = "FAIL"
        result["errors"].append(msg)
        return result

    result["file_size_mb"]  = file_size_mb(path)
    result["sha256_prefix"] = sha256_prefix(path)
    print(f"  Size        : {result['file_size_mb']} MB")
    print(f"  SHA-256 pfx : {result['sha256_prefix']}")

    try:
        # ── 1. Column list (nrows=0 → header only, very fast) ──────────────
        t0 = time.time()
        df_header = pd.read_csv(path, nrows=0)
        columns = list(df_header.columns)
        n_cols = len(columns)
        result["columns"]     = columns
        result["num_columns"] = n_cols
        result["target_found"] = (target in columns) if target else None

        # ── 2. Row count via wc -l (near-instant) ─────────────────────────
        n_rows = wc_lines(path)
        result["total_rows"] = n_rows

        t1 = time.time()
        print(f"  Rows        : {n_rows:,}  (expected {cfg['expected_rows']:,})  "
              f"{'✅' if n_rows == cfg['expected_rows'] else '⚠️  MISMATCH'}")
        print(f"  Columns     : {n_cols}  (expected {cfg['expected_cols']})  "
              f"{'✅' if n_cols == cfg['expected_cols'] else '⚠️  MISMATCH'}")
        print(f"  Header read : {t1-t0:.1f}s")

        result["row_count_ok"] = (n_rows == cfg["expected_rows"])
        result["col_count_ok"] = (n_cols == cfg["expected_cols"])

        # ── 3. Fraud counts (load only the target column) ──────────────────
        if target and result["target_found"]:
            t2 = time.time()
            target_series = pd.read_csv(path, usecols=[target], low_memory=False)[target]
            fraud_count = int((target_series == 1).sum())
            legit_count = int((target_series == 0).sum())
            missing     = int(target_series.isnull().sum())
            t3 = time.time()

            result["fraud_count"]   = fraud_count
            result["legit_count"]   = legit_count
            result["fraud_pct"]     = round(fraud_count / n_rows * 100, 4)

            print(f"  Target      : {target}  ✅")
            print(f"  Fraud (1)   : {fraud_count:,}  ({result['fraud_pct']:.4f}%)")
            print(f"  Legit  (0)  : {legit_count:,}")
            print(f"  Target read : {t3-t2:.1f}s")
        elif target:
            print(f"  Target      : {target}  ❌ NOT FOUND")

        # ── 4. Missing values (load all columns — only for small files) ─────
        if result["file_size_mb"] <= 200:
            t4 = time.time()
            df_full = pd.read_csv(path, low_memory=False)
            result["missing_values"] = int(df_full.isnull().sum().sum())

            # Duplicate check
            if cfg["check_dupes"]:
                result["duplicate_rows"] = int(df_full.duplicated().sum())
            else:
                result["duplicate_rows"] = "SKIPPED (large file)"

            del df_full
            t5 = time.time()
            print(f"  Missing vals: {result['missing_values']:,}")
            print(f"  Duplicates  : {result['duplicate_rows']}")
            print(f"  Full load   : {t5-t4:.1f}s")
        else:
            # For large files use previously verified stats from dataset_stats.json
            result["missing_values"] = "USE_CACHED"
            result["duplicate_rows"] = "SKIPPED (file > 200 MB)"
            print(f"  Missing vals: (see cached stats — file > 200 MB)")
            print(f"  Duplicates  : SKIPPED")

        result["status"] = (
            "PASS" if result["row_count_ok"] and result["col_count_ok"]
                      and result["target_found"] is not False
            else "WARN"
        )

    except Exception as exc:
        result["status"] = "FAIL"
        result["errors"].append(str(exc))
        print(f"  ❌ ERROR: {exc}")

    return result


def main():
    print(f"\n{SEP}")
    print("  FraudGuard AI — Phase 2: Dataset Verification (Fast)")
    print(f"  {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Raw dir: {RAW_DIR}")
    print(SEP)

    results = {}
    t_start = time.time()

    for name, cfg in DATASETS.items():
        results[name] = verify_dataset(name, cfg)

    out_path = REPO_ROOT / "reports" / "phase2_verification_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=4, default=str)

    total = round(time.time() - t_start, 1)

    print(f"\n{SEP}")
    print("  VERIFICATION SUMMARY")
    print(SEP)
    for name, res in results.items():
        icon = "✅" if res["status"] == "PASS" else ("⚠️ " if res["status"] == "WARN" else "❌")
        rows = f"{res['total_rows']:,}" if isinstance(res['total_rows'], int) else "?"
        print(f"  {icon}  {name:30s}  {res['status']:5s}  {rows} rows")

    print(f"\n  Total time : {total}s")
    print(f"  Results    : {out_path}")
    print(SEP + "\n")

    all_ok = all(r["status"] in ("PASS", "WARN") for r in results.values())
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
