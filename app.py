
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import uuid4
from datetime import datetime
from collections import Counter
import json
import re
import math

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
FRONTEND_DIR = ROOT_DIR / "frontend"
ADMIN_TOKEN = "ecce-admin-demo"

app = FastAPI(title="ECCE AskDesk Uganda", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_json(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path: Path, data: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

CHUNKS = load_json(DATA_DIR / "chunks.json", {"chunks": []}).get("chunks", [])
FAQS = load_json(DATA_DIR / "faqs.json", {"faqs": []}).get("faqs", [])
COMPLIANCE = load_json(DATA_DIR / "compliance_items.json", {"items": []}).get("items", [])
ANSWERS: Dict[str, Dict[str, Any]] = {}
FEEDBACK: Dict[str, Dict[str, Any]] = {}

STOP = set("the a an and or of to in for on with is are be by as what who how does do can my me i it this that from through should shall will all under about".split())
TOPICS = {
    "Registration and Licensing": ["registration_licensing", "emis", "standards_compliance"],
    "Standards and Compliance": ["standards_compliance", "inspection_supervision"],
    "Inspection and Support Supervision": ["inspection_supervision", "standards_compliance"],
    "Parents and Communities": ["parent_community_engagement", "communication_awareness"],
    "Teachers and Caregivers": ["teacher_caregiver_support"],
    "Roles and Responsibilities": ["roles_responsibilities"],
}
ROLES = {
    "ECCE Proprietor": ["ECCE Proprietor", "Private Provider"],
    "District Officer": ["District Officer", "Community Leader"],
    "Inspector": ["Inspector", "District Officer"],
    "Teacher/Caregiver": ["Teacher/Caregiver"],
    "Parent/Guardian": ["Parent/Guardian", "Community Leader"],
    "CSO/Partner": ["CSO/Partner", "Development Partner"],
    "MoES Officer": ["MoES Officer"],
}

def toks(text: str) -> List[str]:
    return [w for w in re.findall(r"[a-zA-Z0-9]+", text.lower()) if w not in STOP and len(w) > 1]

def sim(q: str, text: str) -> float:
    qt, ct = Counter(toks(q)), Counter(toks(text))
    if not qt or not ct:
        return 0.0
    overlap = sum(min(qt[k], ct[k]) for k in qt)
    qn = math.sqrt(sum(v * v for v in qt.values()))
    cn = math.sqrt(sum(v * v for v in ct.values()))
    return overlap / (qn * cn) if qn and cn else 0.0

def score(q: str, chunk: Dict[str, Any], role: str = "", topic: str = "") -> float:
    text = " ".join([
        chunk.get("chunk_text", ""),
        chunk.get("section_title", ""),
        " ".join(chunk.get("topic_tags", [])),
        chunk.get("source_label", ""),
    ])
    s = sim(q, text)
    if set(TOPICS.get(topic, [])).intersection(chunk.get("topic_tags", [])):
        s += 0.25
    if set(ROLES.get(role, [role])).intersection(chunk.get("role_tags", [])):
        s += 0.15
    for phrase in ["license", "licence", "registration", "emis", "parent", "community", "inspection", "teacher", "caregiver", "safety", "protection", "local government", "moes", "communication", "baseline", "research"]:
        if phrase in q.lower() and phrase in text.lower():
            s += 0.04
    return s

def retrieve(q: str, role: str, topic: str, k: int = 6) -> List[Dict[str, Any]]:
    matches = []
    for c in CHUNKS:
        sc = score(q, c, role, topic)
        if sc > 0:
            x = dict(c)
            x["score"] = round(sc, 4)
            matches.append(x)
    return sorted(matches, key=lambda x: x["score"], reverse=True)[:k]

def retrieve_faq(q: str, k: int = 3) -> List[Dict[str, Any]]:
    matches = []
    for f in FAQS:
        sc = sim(q, f.get("question", ""))
        if sc > 0:
            x = dict(f)
            x["score"] = round(sc, 4)
            matches.append(x)
    return sorted(matches, key=lambda x: x["score"], reverse=True)[:k]

def detect_risk(q: str) -> str:
    q = q.lower()
    if any(x in q for x in ["approve my licence", "approve my license", "give me a licence", "give me a license", "can you license", "can you approve"]):
        return "licensing_approval"
    if any(x in q for x in ["register my centre", "register my center", "can you register"]):
        return "registration_approval"
    if any(x in q for x in ["legal advice", "sue", "court", "lawyer", "legal opinion"]):
        return "legal_advice"
    if any(x in q for x in ["abuse case", "report abuse", "child abuse", "defilement", "violence against a child"]):
        return "child_protection_case"
    return "normal"

def source_info(chunks: List[Dict[str, Any]]):
    labels, ids = [], []
    for c in chunks[:4]:
        labels.append(c.get("source_label", c.get("chunk_id", "")))
        ids.append(c.get("chunk_id", ""))
    return "; ".join(dict.fromkeys([x for x in labels if x])), list(dict.fromkeys([x for x in ids if x]))

def make_answer(q: str, role: str, topic: str, matches: List[Dict[str, Any]], risk: str) -> Dict[str, Any]:
    src, ids = source_info(matches)
    combined = " ".join(m.get("chunk_text", "") for m in matches[:4])
    lq = q.lower()

    if risk == "child_protection_case":
        return {
            "risk_category": risk,
            "confidence_level": "high",
            "simple_answer": "This tool should not collect child protection case details.",
            "policy_basis": "The ECCE Policy places child welfare, child safety and protection at the centre of ECCE implementation.",
            "next_steps": ["Do not enter a child’s personal details here.", "Use authorised child protection structures immediately.", "Contact the centre manager where safe, the probation officer, Local Government child protection officer or police child and family protection structures."],
            "responsible_actor": "Authorised child protection structures, Local Government officers, probation and family welfare structures, and police child and family protection structures.",
            "source_label": src or "ECCE Policy child safety and protection guidance.",
            "source_chunk_ids": ids,
            "escalation_note": "Use official child protection reporting and referral structures immediately.",
        }

    if risk in ["licensing_approval", "registration_approval"]:
        return {
            "risk_category": risk,
            "confidence_level": "high",
            "simple_answer": "ECCE AskDesk can help you prepare, but it cannot approve, license or register a centre.",
            "policy_basis": "The approved sources assign registration, licensing and regulation functions to MoES, Local Governments and other mandated bodies.",
            "next_steps": ["Use the tool to prepare your documents.", "Contact the District, City or Municipal education office.", "Request the official process.", "Prepare for official verification or inspection."],
            "responsible_actor": "Local Governments handle licensing. MoES provides national policy direction and EMIS-related functions. Proprietors comply with requirements.",
            "source_label": src or "ECCE Policy and implementation standards.",
            "source_chunk_ids": ids,
            "escalation_note": "For official action, contact the relevant Local Government education office or MoES.",
        }

    if not matches:
        return {
            "risk_category": "out_of_scope",
            "confidence_level": "low",
            "simple_answer": "I could not find enough information in the loaded ECCE source material to answer properly.",
            "policy_basis": "The question may need additional source material or official clarification.",
            "next_steps": ["Rephrase the question using ECCE Policy terms.", "Ask about registration, licensing, EMIS, inspection, parent engagement, child safety, MoES or Local Government roles.", "Consult MoES or the relevant Local Government authority for official clarification."],
            "responsible_actor": "MoES or the relevant Local Government authority.",
            "source_label": "No strong source match.",
            "source_chunk_ids": [],
            "escalation_note": "Seek official clarification where the issue affects approval, licensing, registration, enforcement or child safety.",
        }

    if "license" in lq or "licence" in lq:
        simple = "ECCE licensing is handled through the relevant Local Government authority, with MoES providing national policy direction and standards."
        steps = ["Contact the District, City or Municipal education office.", "Confirm the official licensing pathway for your service category.", "Prepare ownership, location, staffing, safety and facility information.", "Complete a standards self-check before inspection or verification."]
        actor = "Local Governments license and regulate ECCE services. Proprietors comply. MoES provides standards."
    elif "register" in lq or "emis" in lq:
        simple = "Registration and EMIS onboarding require accurate centre information and supporting documents."
        steps = ["Prepare a formal application for registration on EMIS.", "Obtain proof of Local Government registration where applicable.", "Identify the nearest primary school and its EMIS number.", "Submit information through the official channel advised by MoES or Local Government."]
        actor = "MoES manages EMIS registration and profiling. Local Governments support verification and licensing. Proprietors prepare information."
    elif "parent" in lq or "community" in lq:
        simple = "Parents and communities should be mobilised to understand the value of ECCE and support children’s early learning, safety and development."
        steps = ["Use simple, parent-friendly language.", "Explain safety, play, school readiness and the value of ECCE.", "Invite parents to ask questions.", "Create a safe way for parents to report concerns."]
        actor = "MoES, Local Governments, centres, CSOs, community leaders and parents all have roles."
    elif "local government" in lq or "district" in lq:
        simple = "Local Governments plan, budget, license, regulate, inspect, monitor and mobilise communities for ECCE implementation."
        steps = ["Assign ECCE responsibilities within the district structure.", "Map ECCE centres.", "Plan and budget for ECCE implementation.", "Coordinate licensing, inspection and community mobilisation."]
        actor = "City, District, Municipal and Local Government authorities."
    else:
        simple = combined.split(".")[0].strip() + "."
        steps = ["Review the source guidance.", "Identify the responsible actor.", "Prepare the required action or documents.", "Seek official clarification where approval or interpretation is required."]
        actor = "Responsibility depends on the issue. The source guidance identifies the relevant actors."

    return {
        "risk_category": risk,
        "confidence_level": "high" if matches[0].get("score", 0) > 0.25 else "medium",
        "simple_answer": simple,
        "policy_basis": combined[:1100] + ("..." if len(combined) > 1100 else ""),
        "next_steps": steps,
        "responsible_actor": actor,
        "source_label": src,
        "source_chunk_ids": ids,
        "escalation_note": "For official approval, licensing, registration, enforcement or legal interpretation, contact MoES or the relevant Local Government authority.",
    }

class AskReq(BaseModel):
    session_id: Optional[str] = None
    question: str
    selected_role: str = "District Officer"
    selected_topic: str = "Ask the ECCE Policy"

class RetrieveReq(BaseModel):
    question: str
    selected_role: str = "District Officer"
    selected_topic: str = "Ask the ECCE Policy"
    top_k: int = 6

class ComplianceReq(BaseModel):
    session_id: Optional[str] = None
    selected_role: str = "ECCE Proprietor"
    checked_item_ids: List[str] = []

class ChecklistReq(BaseModel):
    selected_role: str = "ECCE Proprietor"
    checklist_type: str = "Licensing preparation"
    selected_topic: str = "Registration and Licensing"

class FeedbackReq(BaseModel):
    answer_record_id: str
    feedback_type: str
    feedback_comment: Optional[str] = None

class ImportReq(BaseModel):
    chunks: List[Dict[str, Any]]

@app.get("/api/status")
def api_status():
    return {"name": "ECCE AskDesk Uganda", "status": "running", "chunks": len(CHUNKS), "faqs": len(FAQS), "compliance_items": len(COMPLIANCE)}

@app.post("/api/retrieve")
def api_retrieve(p: RetrieveReq):
    return {"matches": retrieve(p.question, p.selected_role, p.selected_topic, p.top_k), "faq_matches": retrieve_faq(p.question, 3)}

@app.post("/api/ask")
def api_ask(p: AskReq):
    risk = detect_risk(p.question)
    matches = retrieve(p.question, p.selected_role, p.selected_topic, 6)
    f = retrieve_faq(p.question, 1)
    if f and f[0].get("score", 0) > 0.35:
        ids = set(f[0].get("primary_chunk_ids", []))
        fm = [c for c in CHUNKS if c.get("chunk_id") in ids]
        matches = fm + [x for x in matches if x.get("chunk_id") not in ids]
    a = make_answer(p.question, p.selected_role, p.selected_topic, matches, risk)
    aid = str(uuid4())
    rec = {"answer_record_id": aid, "session_id": p.session_id, "question": p.question, "selected_role": p.selected_role, "selected_topic": p.selected_topic, "created_at": datetime.utcnow().isoformat(), **a}
    ANSWERS[aid] = rec
    return rec

@app.get("/api/faqs")
def api_faqs():
    return {"faqs": FAQS, "count": len(FAQS)}

@app.get("/api/compliance/items")
def api_compliance_items():
    return {"items": COMPLIANCE}

@app.post("/api/compliance/score")
def api_compliance_score(p: ComplianceReq):
    total = len(COMPLIANCE)
    checked = set(p.checked_item_ids)
    unchecked = [i for i in COMPLIANCE if i.get("item_id") not in checked]
    pct = round((len(checked) / total) * 100) if total else 0
    if pct >= 75:
        cat, note = "Mostly ready", "The centre appears close to readiness, subject to official verification."
    elif pct >= 45:
        cat, note = "Needs improvement", "Several gaps should be addressed before inspection or renewal."
    else:
        cat, note = "Urgent action needed", "The centre needs immediate follow-up before it can be treated as inspection-ready."
    return {
        "score_percent": pct,
        "readiness_category": cat,
        "checked_count": len(checked),
        "total_count": total,
        "unchecked_items": [{"item_id": i.get("item_id"), "compliance_area": i.get("compliance_area"), "corrective_action": i.get("corrective_action"), "source_label": i.get("source_label")} for i in unchecked],
        "note": note,
        "disclaimer": "This is a self-check only. Official registration, licensing, inspection and compliance decisions remain with MoES, Local Governments and relevant statutory bodies.",
    }

@app.post("/api/checklist/generate")
def api_checklist(p: ChecklistReq):
    t = (p.checklist_type + " " + p.selected_topic).lower()
    if "licens" in t or "registration" in t:
        title = "ECCE Centre Registration and Licensing Preparation Checklist"
        items = ["Confirm the service category: day care, pre-primary, home-based, community-based, kindergarten or nursery.", "Prepare centre ownership and management details.", "Prepare location details and nearest primary school EMIS number.", "Compile teacher and caregiver records.", "Prepare proof of Local Government registration where applicable.", "Complete a child safety and learning environment self-check.", "Contact the Local Government education office for official licensing."]
        source = "ECCE Policy, Standards and Guidelines on registration, licensing and EMIS onboarding."
    elif "community" in t or "parent" in t:
        title = "Parent and Community Dialogue Checklist"
        items = ["Define the purpose of the dialogue.", "Prepare simple messages on the value of ECCE.", "Invite parents, caregivers, local leaders, VHTs, teachers and centre managers.", "Include child safety, play, school readiness and parent responsibilities.", "Explain how parents can report concerns.", "Document questions, commitments and follow-up actions."]
        source = "ECCE Policy guidance on parent and community engagement."
    else:
        title = "ECCE Implementation Checklist"
        items = ["Confirm the relevant ECCE Policy requirement.", "Identify the responsible institution or officer.", "Prepare required documents or information.", "Check compliance against approved standards.", "Record the next action, person responsible and deadline."]
        source = "ECCE Policy and implementation standards."
    return {"title": title, "items": items, "source_label": source, "disclaimer": "This checklist supports preparation only. It is not an official licence, registration certificate, inspection result or approval."}

@app.post("/api/feedback")
def api_feedback(p: FeedbackReq):
    fid = str(uuid4())
    FEEDBACK[fid] = p.model_dump()
    return {"status": "received", "message": "Thank you. Your feedback has been recorded."}

@app.get("/api/admin/analytics/summary")
def api_analytics():
    return {"total_answers": len(ANSWERS), "total_feedback": len(FEEDBACK), "loaded_chunks": len(CHUNKS), "loaded_faqs": len(FAQS), "loaded_compliance_items": len(COMPLIANCE)}

@app.post("/api/admin/chunks/import")
def api_import_chunks(p: ImportReq, x_admin_token: Optional[str] = Header(default=None)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid admin token")
    existing = {c.get("chunk_id") for c in CHUNKS}
    added, updated = 0, 0
    for c in p.chunks:
        if "chunk_id" not in c or "chunk_text" not in c:
            continue
        if c["chunk_id"] in existing:
            for i, old in enumerate(CHUNKS):
                if old.get("chunk_id") == c["chunk_id"]:
                    CHUNKS[i] = c
                    updated += 1
                    break
        else:
            CHUNKS.append(c)
            existing.add(c["chunk_id"])
            added += 1
    save_json(DATA_DIR / "chunks.json", {"chunks": CHUNKS})
    return {"status": "ok", "added": added, "updated": updated, "total_chunks": len(CHUNKS)}

# Static frontend routes are registered after API routes.
if (FRONTEND_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")
if (FRONTEND_DIR / "resources").exists():
    app.mount("/resources", StaticFiles(directory=str(FRONTEND_DIR / "resources")), name="resources")

@app.get("/", include_in_schema=False)
def serve_home():
    return FileResponse(str(FRONTEND_DIR / "index.html"))

@app.get("/app", include_in_schema=False)
def serve_app():
    return FileResponse(str(FRONTEND_DIR / "index.html"))

@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend_fallback(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")
    return FileResponse(str(FRONTEND_DIR / "index.html"))
