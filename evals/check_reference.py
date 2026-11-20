"""Validate golden-question references using app_reader, without invoking an LLM.

Run from the project root: python evals/check_reference.py
Credentials come only from APP_DATABASE_URL in the environment or local .env.
"""

import argparse
import csv
import json
import logging
import os
from pathlib import Path
import re
import sys

import psycopg
from dotenv import dotenv_values


ROOT = Path(__file__).resolve().parents[1]
COLUMNS = ["id", "question", "category", "reference_sql", "correct_behavior", "source"]
CATEGORIES = {"lookup", "aggregate", "trend", "compare", "should_decline"}


def read_questions(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle, strict=True)
        if reader.fieldnames != COLUMNS:
            raise ValueError("CSV must have the six required columns in the expected order.")
        questions = list(reader)
    if len(questions) < 15:
        raise ValueError("At least 15 golden questions are required.")
    ids = set()
    for row in questions:
        if set(row) != set(COLUMNS) or any(value is None for value in row.values()):
            raise ValueError("CSV has a missing or extra field.")
        identifier = row["id"]
        if not re.fullmatch(r"[1-9][0-9]*", identifier) or identifier in ids:
            raise ValueError("Question IDs must be unique positive integers.")
        ids.add(identifier)
        if row["category"] not in CATEGORIES or row["source"] not in {"baseline", "other"}:
            raise ValueError("CSV has an unsupported category or source.")
        if not row["question"].strip() or not row["correct_behavior"].strip():
            raise ValueError("Question and correct behavior must be nonempty.")
        query = row["reference_sql"]
        if row["category"] == "should_decline":
            if query != "":
                raise ValueError("should_decline reference SQL must be completely empty.")
            continue
        # A conservative precheck for these reviewed references, not a general SQL parser.
        # Ignore quoted literals/identifiers before checking statement boundaries/tokens.
        scrubbed = re.sub(r"'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"", "", query).strip()
        if not re.match(r"^(select|with)\b", scrubbed, re.IGNORECASE):
            raise ValueError("Answerable questions require a SELECT or WITH query.")
        if ";" in scrubbed.removesuffix(";") or "--" in scrubbed or "/*" in scrubbed:
            raise ValueError("References must be single statements without SQL comments.")
        if re.search(
            r"\b(insert|update|delete|truncate|create|alter|drop|grant|revoke|copy|call|do|"
            r"set|reset|commit|rollback|into|nextval|setval|set_config|pg_sleep|dblink|"
            r"pg_read_file|lo_export)\b", scrubbed, re.IGNORECASE
        ):
            raise ValueError("Reference contains an unsupported SQL operation.")
    if {row["category"] for row in questions} != CATEGORIES:
        raise ValueError("All five required categories must be represented.")
    if sum(row["source"] == "baseline" for row in questions) < 8:
        raise ValueError("At least eight questions must have baseline provenance.")
    if sum(row["category"] == "should_decline" for row in questions) < 3:
        raise ValueError("At least three should_decline questions are required.")
    return questions


def safe_sqlstate(error):
    code = getattr(error, "sqlstate", None)
    return code if isinstance(code, str) and re.fullmatch(r"[A-Z0-9]{5}", code) else "unavailable"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=ROOT / "evals" / "golden_questions.csv")
    parser.add_argument("--max-rows", type=int, default=25,
                        help="Maximum answer rows displayed per question (default: 25)")
    args = parser.parse_args()
    if args.max_rows < 1:
        parser.error("--max-rows must be positive")
    try:
        questions = read_questions(args.csv)
    except (OSError, ValueError, csv.Error, UnicodeError):
        print("CSV validation: FAILED. Check columns, IDs, labels, provenance, and reference SQL.")
        return 1
    print(f"CSV validation: PASSED ({len(questions)} questions)")

    connection = None
    failed = 0
    passed = 0
    skipped = 0
    try:
        # Do not allow dotenv parse warnings to expose local configuration details.
        logging.getLogger("dotenv.main").disabled = True
        url = os.environ.get("APP_DATABASE_URL")
        if not url:
            url = dotenv_values(ROOT / ".env", interpolate=False).get("APP_DATABASE_URL")
        if not url:
            print("Connection: FAILED. APP_DATABASE_URL is not configured.")
            return 1
        # Never fall back to a setup/owner or loader connection.
        connection = psycopg.connect(url, connect_timeout=10, autocommit=True)
        with connection.transaction():
            connection.execute("SET TRANSACTION READ ONLY")
            connection.execute("SET LOCAL statement_timeout = '15s'")
            if not connection.execute("SELECT current_user = 'app_reader'").fetchone()[0]:
                print("Role verification: FAILED. Expected app_reader; no references executed.")
                return 1
        print("Connection and app_reader identity: PASSED")

        for row in questions:
            label = f"Question {row['id']} [{row['category']}]"
            if row["category"] == "should_decline":
                print(f"{label}: SKIPPED — empty reference SQL verified; decline behavior requires later evaluation.")
                skipped += 1
                continue
            try:
                with connection.transaction():
                    connection.execute("SET TRANSACTION READ ONLY")
                    connection.execute("SET LOCAL statement_timeout = '30s'")
                    connection.execute("SET LOCAL lock_timeout = '3s'")
                    connection.execute("SET LOCAL TIME ZONE 'UTC'")
                    connection.execute("SET LOCAL extra_float_digits = 3")
                    with connection.cursor(binary=True) as cursor:
                        # Prepared execution also rejects multiple SQL commands.
                        cursor.execute(row["reference_sql"], prepare=True)
                        columns = [column.name for column in cursor.description]
                        answers = cursor.fetchmany(args.max_rows + 1)
                        if not answers:
                            print(f"{label}: FAILED — empty result; review current scope and data.")
                            failed += 1
                            continue
                        print(f"{label}: PASSED")
                        for answer in answers[:args.max_rows]:
                            print("  " + json.dumps(dict(zip(columns, answer)), default=str, ensure_ascii=False))
                        if len(answers) > args.max_rows:
                            print(f"  Answer preview limited to {args.max_rows} rows; use --max-rows to display more.")
                passed += 1
            except psycopg.Error as error:
                # Transaction context rolls back the failed query before continuing.
                print(f"{label}: FAILED — SQLSTATE {safe_sqlstate(error)}; details withheld.")
                failed += 1
                if connection.closed or connection.broken:
                    print("Connection unavailable; remaining references were not executed.")
                    return 1
        print(f"Summary: {passed} references passed, {failed} failed, {skipped} decline questions skipped.")
        return 1 if failed else 0
    except Exception:
        print("Checker stopped: connection or local processing failure; details withheld.")
        return 1
    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(main())
