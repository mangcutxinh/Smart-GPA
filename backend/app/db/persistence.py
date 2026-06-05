import os
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict

logger = logging.getLogger("smartgpa.persistence")

# File path inside the workspace
DB_DUMP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage_mock", "mock_db_dump.json")

def _datetime_encoder(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return {"__type__": "datetime", "value": obj.isoformat()}
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

def _custom_decoder(dct: Dict[str, Any]) -> Any:
    if "__type__" in dct and dct["__type__"] == "datetime":
        val = dct["value"]
        # Replace Z with +00:00 for older python compatibility
        if val.endswith("Z"):
            val = val[:-1] + "+00:00"
        return datetime.fromisoformat(val)
    return dct

def save_db_to_disk() -> bool:
    try:
        from app.db.real_db import (
            USERS_DB, COURSES_DB, ASSIGNMENTS_DB, ACTIVITY_LOGS,
            TIMELINE_UPDATES, WARNING_ACTIONS, SCORE_HISTORY_DB,
            PROJECT_INFO, GRADING_RULES_DB, CURRENT_SEMESTER,
            DEPARTMENTS_DB, INSTITUTES_DB, MAJORS_DB
        )
        from app.db.databricks_db import MOCK_GOLD_DB

        # Format MOCK_GOLD_DB string keys
        serialized_gold = {}
        for key, val in MOCK_GOLD_DB.items():
            if isinstance(key, tuple) and len(key) == 2:
                str_key = f"{key[0]}##{key[1]}"
            else:
                str_key = str(key)
            serialized_gold[str_key] = val

        data_to_dump = {
            "USERS_DB": USERS_DB,
            "MOCK_GOLD_DB": serialized_gold,
            "COURSES_DB": COURSES_DB,
            "ASSIGNMENTS_DB": ASSIGNMENTS_DB,
            "ACTIVITY_LOGS": ACTIVITY_LOGS,
            "TIMELINE_UPDATES": TIMELINE_UPDATES,
            "WARNING_ACTIONS": WARNING_ACTIONS,
            "SCORE_HISTORY_DB": SCORE_HISTORY_DB,
            "PROJECT_INFO": PROJECT_INFO,
            "GRADING_RULES_DB": GRADING_RULES_DB,
            "CURRENT_SEMESTER": CURRENT_SEMESTER,
            "DEPARTMENTS_DB": DEPARTMENTS_DB,
            "INSTITUTES_DB": INSTITUTES_DB,
            "MAJORS_DB": MAJORS_DB
        }

        os.makedirs(os.path.dirname(DB_DUMP_PATH), exist_ok=True)
        with open(DB_DUMP_PATH, "w", encoding="utf-8") as f:
            json.dump(data_to_dump, f, indent=2, ensure_ascii=False, default=_datetime_encoder)
        logger.info(f"Successfully saved database backup to {DB_DUMP_PATH}")
        return True
    except Exception as e:
        logger.error(f"Failed to save database backup: {e}", exc_info=True)
        return False

def load_db_from_disk() -> bool:
    if not os.path.exists(DB_DUMP_PATH):
        logger.info(f"No database backup found at {DB_DUMP_PATH}. Starting with standard seed data.")
        return False

    try:
        from app.db.real_db import (
            USERS_DB, COURSES_DB, ASSIGNMENTS_DB, ACTIVITY_LOGS,
            TIMELINE_UPDATES, WARNING_ACTIONS, SCORE_HISTORY_DB,
            PROJECT_INFO, GRADING_RULES_DB, CURRENT_SEMESTER,
            DEPARTMENTS_DB, INSTITUTES_DB, MAJORS_DB
        )
        from app.db.databricks_db import MOCK_GOLD_DB, sync_gold_to_silver

        with open(DB_DUMP_PATH, "r", encoding="utf-8") as f:
            data = json.load(f, object_hook=_custom_decoder)

        # Helper to safely clear and update in place
        def inplace_update(target: Any, source: Any):
            if isinstance(target, dict) and isinstance(source, dict):
                target.clear()
                target.update(source)
            elif isinstance(target, list) and isinstance(source, list):
                target.clear()
                target.extend(source)

        if "USERS_DB" in data:
            inplace_update(USERS_DB, data["USERS_DB"])
        if "COURSES_DB" in data:
            inplace_update(COURSES_DB, data["COURSES_DB"])
        if "ASSIGNMENTS_DB" in data:
            inplace_update(ASSIGNMENTS_DB, data["ASSIGNMENTS_DB"])
        if "ACTIVITY_LOGS" in data:
            inplace_update(ACTIVITY_LOGS, data["ACTIVITY_LOGS"])
        if "TIMELINE_UPDATES" in data:
            inplace_update(TIMELINE_UPDATES, data["TIMELINE_UPDATES"])
        if "WARNING_ACTIONS" in data:
            inplace_update(WARNING_ACTIONS, data["WARNING_ACTIONS"])
        if "SCORE_HISTORY_DB" in data:
            inplace_update(SCORE_HISTORY_DB, data["SCORE_HISTORY_DB"])
        if "PROJECT_INFO" in data:
            inplace_update(PROJECT_INFO, data["PROJECT_INFO"])
        if "GRADING_RULES_DB" in data:
            inplace_update(GRADING_RULES_DB, data["GRADING_RULES_DB"])
        if "CURRENT_SEMESTER" in data:
            inplace_update(CURRENT_SEMESTER, data["CURRENT_SEMESTER"])
        if "DEPARTMENTS_DB" in data:
            inplace_update(DEPARTMENTS_DB, data["DEPARTMENTS_DB"])
        if "INSTITUTES_DB" in data:
            inplace_update(INSTITUTES_DB, data["INSTITUTES_DB"])
        if "MAJORS_DB" in data:
            inplace_update(MAJORS_DB, data["MAJORS_DB"])

        if "MOCK_GOLD_DB" in data:
            deserialized_gold = {}
            for k, val in data["MOCK_GOLD_DB"].items():
                if "##" in k:
                    parts = k.split("##", 1)
                    deserialized_gold[(parts[0], parts[1])] = val
                else:
                    deserialized_gold[k] = val
            MOCK_GOLD_DB.clear()
            MOCK_GOLD_DB.update(deserialized_gold)
            sync_gold_to_silver()

        logger.info(f"Successfully loaded database backup from {DB_DUMP_PATH}")
        return True
    except Exception as e:
        logger.error(f"Failed to load database backup: {e}", exc_info=True)
        return False
