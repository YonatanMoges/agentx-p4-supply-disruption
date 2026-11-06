"""FastAPI bridge for the P4 Supply Disruption Responder practice simulator.

Keep this file next to common.py and p4_supply_api.py. Place the workbook in
./data/P4_Supply_Disruption_Data.xlsx (or alongside this file).

Run with one worker and no --reload so all n8n workflows share one session:
    uvicorn bridge:app --host 127.0.0.1 --port 8000

For n8n running in Docker Desktop, bind to 0.0.0.0 and limit network exposure.
Set P4_API_KEY in your environment before starting the server.
"""

import os
import secrets
import threading
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from p4_supply_api import SupplyAPI

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "P4_Supply_Disruption_Data.xlsx"
if not DATA_FILE.exists():
    DATA_FILE = BASE_DIR / "P4_Supply_Disruption_Data.xlsx"
if not DATA_FILE.exists():
    raise RuntimeError("Workbook not found: put P4_Supply_Disruption_Data.xlsx in data/")

API_KEY = os.getenv("P4_API_KEY")
if not API_KEY:
    raise RuntimeError("Set the P4_API_KEY environment variable before starting FastAPI")

app = FastAPI(title="P4 SupplyAPI Bridge", version="1.0")
lock = threading.Lock()
api = SupplyAPI("practice_01", data_xlsx=str(DATA_FILE))


class ToolRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class SessionRequest(BaseModel):
    scenario: str = "practice_01"


def require_api_key(x_api_key: str | None = Header(default=None)):
    if x_api_key is None or not secrets.compare_digest(x_api_key, API_KEY):
        raise HTTPException(status_code=401, detail="Missing or incorrect X-API-Key")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tools", dependencies=[Depends(require_api_key)])
def tools():
    return SupplyAPI.tool_schemas()


@app.post("/start", dependencies=[Depends(require_api_key)])
def start_session(request: SessionRequest):
    global api
    if request.scenario not in {f"practice_{n:02d}" for n in range(1, 6)}:
        raise HTTPException(status_code=400, detail="Use practice_01 through practice_05")
    with lock:
        # A new SupplyAPI session resets time, quotes, POs, and this scenario's log.
        api = SupplyAPI(request.scenario, data_xlsx=str(DATA_FILE))
        current = api.call("get_current_time")
    return {"scenario": request.scenario, **current}


def validate_email_call(arguments: dict[str, Any]) -> None:
    """Block unsafe sends before the simulator can record a rule violation."""
    to = str(arguments.get("to", ""))
    domain = to.rsplit("@", 1)[-1].lower() if "@" in to else ""
    if domain not in api.domains and not (domain == "uni.example" or domain.endswith(".uni.example")):
        raise HTTPException(status_code=400, detail="Recipient email domain is not trusted")

    po_id = arguments.get("po_id")
    if po_id:
        draft = api.drafts.get(po_id)
        if draft is None:
            raise HTTPException(status_code=400, detail="PO does not exist")
        if draft["approval_required"] and not draft["approved"]:
            raise HTTPException(status_code=403, detail="PO requires approval before sending")
        expected_domain = str(api.sup.loc[draft["supplier_id"], "email_domain"]).lower()
        if domain != expected_domain:
            raise HTTPException(status_code=400, detail="PO recipient is not the selected supplier")


@app.post("/call", dependencies=[Depends(require_api_key)])
def call_tool(request: ToolRequest):
    with lock:
        if request.name not in {item["name"] for item in SupplyAPI.tool_schemas()}:
            raise HTTPException(status_code=400, detail="Unknown SupplyAPI tool")
        if request.name == "send_email":
            validate_email_call(request.arguments)
        result = api.call(request.name, request.arguments)
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result


@app.get("/summary", dependencies=[Depends(require_api_key)])
def summary():
    with lock:
        return api.run_summary()



@app.get("/suppliers", dependencies=[Depends(require_api_key)])
def get_suppliers():
    with lock:
        suppliers = api.sup.reset_index()
        return suppliers[
            ["supplier_id", "supplier_name", "email_domain"]
        ].to_dict(orient="records")
