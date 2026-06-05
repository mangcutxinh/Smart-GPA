import base64
import time
from typing import Any, Dict

import httpx

from app.core.config import settings


class DatabricksPipelineError(RuntimeError):
    pass


def _workspace_host() -> str:
    host = settings.DATABRICKS_SERVER_HOSTNAME or settings.DATABRICKS_HOST.replace("https://", "")
    return host.strip().rstrip("/")


def _api_base() -> str:
    host = _workspace_host()
    if not host:
        raise DatabricksPipelineError("Missing DATABRICKS_SERVER_HOSTNAME.")
    return f"https://{host}"


def _headers() -> Dict[str, str]:
    if not settings.DATABRICKS_TOKEN:
        raise DatabricksPipelineError("Missing DATABRICKS_TOKEN.")
    return {"Authorization": f"Bearer {settings.DATABRICKS_TOKEN}"}


def _require_job_id() -> int:
    if not settings.DATABRICKS_JOB_ID:
        raise DatabricksPipelineError("Missing DATABRICKS_JOB_ID.")
    try:
        return int(settings.DATABRICKS_JOB_ID)
    except ValueError as exc:
        raise DatabricksPipelineError("DATABRICKS_JOB_ID must be a number.") from exc


def upload_csv_to_workspace_files(filename: str, contents: bytes) -> str:
    safe_filename = filename.replace("\\", "_").replace("/", "_")
    upload_dir = (settings.DATABRICKS_UPLOAD_DIR or "/Shared/smartgpa_uploads").strip().rstrip("/")
    if not upload_dir.startswith("/"):
        upload_dir = f"/{upload_dir}"
    if upload_dir.startswith("/Workspace/"):
        upload_dir = upload_dir.removeprefix("/Workspace")
    if upload_dir.startswith("/Users/"):
        raise DatabricksPipelineError(
            "DATABRICKS_UPLOAD_DIR dang tro vao /Users. Vui long doi sang /Shared/smartgpa_uploads."
        )
    workspace_path = f"{upload_dir}/{safe_filename}"
    workspace_files_path = f"/Workspace{workspace_path}"
    notebook_read_path = f"file:{workspace_files_path}"

    with httpx.Client(timeout=60) as client:
        mkdirs_response = client.post(
            f"{_api_base()}/api/2.0/workspace/mkdirs",
            headers=_headers(),
            json={"path": upload_dir},
        )
        if mkdirs_response.status_code >= 400:
            raise DatabricksPipelineError(f"Workspace mkdirs failed: {mkdirs_response.text}")

        files_response = client.put(
            f"{_api_base()}/api/2.0/workspace-files/import-file{workspace_files_path}",
            headers=_headers(),
            params={"overwrite": "true"},
            content=contents,
        )
        if files_response.status_code < 400:
            return notebook_read_path

        response = client.post(
            f"{_api_base()}/api/2.0/workspace/import",
            headers=_headers(),
            json={
                "path": workspace_path,
                "format": "AUTO",
                "content": base64.b64encode(contents).decode("ascii"),
                "overwrite": True,
            },
        )
    if response.status_code >= 400:
        raise DatabricksPipelineError(
            "Databricks Workspace file upload failed: "
            f"{files_response.text}; workspace import fallback failed: {response.text}"
        )

    return notebook_read_path


def run_pipeline_job(csv_path: str) -> Dict[str, Any]:
    job_id = _require_job_id()
    payload = {
        "job_id": job_id,
        "notebook_params": {
            "csv_path": csv_path,
        },
    }

    with httpx.Client(timeout=60) as client:
        response = client.post(
            f"{_api_base()}/api/2.2/jobs/run-now",
            headers=_headers(),
            json=payload,
        )
    if response.status_code >= 400:
        raise DatabricksPipelineError(f"Databricks job run-now failed: {response.text}")

    return response.json()


def wait_for_run(run_id: int) -> Dict[str, Any]:
    deadline = time.time() + settings.DATABRICKS_JOB_TIMEOUT_SECONDS

    with httpx.Client(timeout=60) as client:
        while time.time() < deadline:
            response = client.get(
                f"{_api_base()}/api/2.2/jobs/runs/get",
                headers=_headers(),
                params={"run_id": run_id},
            )
            if response.status_code >= 400:
                raise DatabricksPipelineError(f"Databricks run status failed: {response.text}")

            run = response.json()
            state = run.get("state", {})
            life_cycle_state = state.get("life_cycle_state")
            result_state = state.get("result_state")

            if life_cycle_state in {"TERMINATED", "SKIPPED", "INTERNAL_ERROR"}:
                if result_state == "SUCCESS":
                    return run
                message = state.get("state_message") or result_state or life_cycle_state
                raise DatabricksPipelineError(f"Databricks job did not succeed: {message}")

            time.sleep(5)

    raise DatabricksPipelineError("Databricks job timed out.")


def get_run_output(run_id: int) -> Dict[str, Any]:
    with httpx.Client(timeout=60) as client:
        response = client.get(
            f"{_api_base()}/api/2.2/jobs/runs/get-output",
            headers=_headers(),
            params={"run_id": run_id},
        )
    if response.status_code >= 400:
        raise DatabricksPipelineError(f"Databricks run output failed: {response.text}")
    return response.json()


def upload_and_run_pipeline(filename: str, contents: bytes) -> Dict[str, Any]:
    csv_path = upload_csv_to_workspace_files(filename, contents)
    run_now = run_pipeline_job(csv_path)
    run_id = run_now.get("run_id")
    if not run_id:
        raise DatabricksPipelineError(f"Databricks run-now response missing run_id: {run_now}")

    run = wait_for_run(int(run_id))
    try:
        output = get_run_output(int(run_id))
    except DatabricksPipelineError:
        output = None

    return {
        "csv_path": csv_path,
        "workspace_path": csv_path.removeprefix("file:/Workspace"),
        "run_id": run_id,
        "run_page_url": run.get("run_page_url"),
        "state": run.get("state"),
        "output": output,
    }


def upload_and_trigger_pipeline(filename: str, contents: bytes) -> Dict[str, Any]:
    csv_path = upload_csv_to_workspace_files(filename, contents)
    run_now = run_pipeline_job(csv_path)
    run_id = run_now.get("run_id")
    if not run_id:
        raise DatabricksPipelineError(f"Databricks run-now response missing run_id: {run_now}")
    return {
        "csv_path": csv_path,
        "workspace_path": csv_path.removeprefix("file:/Workspace"),
        "run_id": run_id,
        "pipeline_status": "RUNNING",
    }



def check_run_status(run_id: int) -> Dict[str, Any]:
    with httpx.Client(timeout=10) as client:
        response = client.get(
            f"{_api_base()}/api/2.2/jobs/runs/get",
            headers=_headers(),
            params={"run_id": run_id},
        )
        if response.status_code >= 400:
            raise DatabricksPipelineError(f"Databricks run status check failed: {response.text}")
        run = response.json()
        state = run.get("state", {})
        life_cycle_state = state.get("life_cycle_state")
        result_state = state.get("result_state")
        
        status_str = "RUNNING"
        if life_cycle_state in {"TERMINATED", "SKIPPED", "INTERNAL_ERROR"}:
            if result_state == "SUCCESS":
                status_str = "SUCCESS"
            else:
                status_str = "FAILED"
        return {
            "status": status_str,
            "life_cycle_state": life_cycle_state,
            "result_state": result_state,
            "message": state.get("state_message") or ""
        }
