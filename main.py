import psycopg2
import bcrypt
import secrets
from datetime import datetime
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

active_tokens = {}

def get_db():
    return psycopg2.connect(
        host="localhost",
        port="5432",
        database="onboarding",
        user="postgres",
        password="parola"
    )

class LoginData(BaseModel):
    username: str
    password: str
 
class TicketCreate(BaseModel):
    employee_name: str
    role: str
    start_date: str
    hardware: str

class TicketEdit(BaseModel):
    employee_name: str
    role: str
    start_date: str
    hardware: str


def verify_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="no token")
    parts = authorization.split()
    if len(parts) != 2 or parts[0] != "Bearer":
        raise HTTPException(status_code=401, detail="invalid token")
    
    token = parts[1]
    if token not in active_tokens:
        raise HTTPException(status_code=401, detail="token invalid/expirat")
    
    return active_tokens[token]


@app.post("/login")
def login(data: LoginData):
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT id, password_hash, role FROM users WHERE username = %s", (data.username,))
    user = c.fetchone()

    c.close()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="user gresit")
 
    user_id, stored_hash, role = user

    if not bcrypt.checkpw(data.password.encode("utf-8"), stored_hash.encode("utf-8")):
        raise HTTPException(status_code=401, detail="parola gresita")
    
    token = secrets.token_hex(16)
    active_tokens[token] = {"user_id": user_id, "role": role}

    return {"token": token, "user_id": user_id, "role": role}


@app.post("/tickets")
def create_ticket(ticket: TicketCreate, authorization: str = Header(None)):
    user_data = verify_token(authorization)
    if user_data["role"] != "HR":
        raise HTTPException(status_code = 403, detail="doar HR-ul poate crea tickets")
    
    conn = get_db()
    c = conn.cursor()
    status = "PENDING_MANAGER"
    time_now = datetime.now().isoformat()

    c.execute("""
        INSERT INTO tickets (employee_name, role, start_date, hardware, status, created_by)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (ticket.employee_name, ticket.role, ticket.start_date, ticket.hardware, status, user_data["user_id"]))

    ticket_id = c.fetchone()[0]
    
    c.execute("""
        INSERT INTO history (ticket_id, user_id, stage, created_at)
        VALUES (%s, %s, %s, %s)
    """, (ticket_id, user_data["user_id"], "PENDING_MANAGER", time_now))

    conn.commit()
    c.close()
    conn.close()

    return {"ticket_id": ticket_id, "status": status}


@app.get("/tickets")
def get_tickets(authorization: str = Header(None)):
    user_data = verify_token(authorization)
    role = user_data["role"]

    conn = get_db()
    c = conn.cursor()

    if role == "HR":
        c.execute("SELECT * FROM tickets ORDER BY created_at DESC")
    elif role == "Manager":
        c.execute("SELECT * FROM tickets WHERE status = 'PENDING_MANAGER' ORDER BY created_at DESC")
    elif role == "Finance":
        c.execute("SELECT * FROM tickets WHERE status = 'PENDING_FINANCE' ORDER BY created_at DESC")
    elif role == "IT":
        c.execute("SELECT * FROM tickets WHERE status = 'PENDING_IT' ORDER BY created_at DESC")
    else:
        c.close()
        conn.close()
        return []
    
    rows = c.fetchall()
    c.close()
    conn.close()

    tickets = []
    for r in rows:
        tickets.append({
            "id": r[0],
            "employee_name": r[1],
            "role": r[2],
            "start_date": str(r[3]),
            "hardware": r[4],
            "status": r[5],
            "created_by": r[6],
        })
 
    return tickets


@app.post("/tickets/{ticket_id}/approve")
def approve_ticket(ticket_id: int, authorization: str = Header(None)):
    user_data = verify_token(authorization)
    role = user_data["role"]
    user_id = user_data["user_id"]
    
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT status, hardware FROM tickets WHERE id = %s", (ticket_id,))
    row = c.fetchone()

    if not row:
        c.close()
        conn.close()
        raise HTTPException(status_code=404, detail="nu exista tichetul")
    
    status, hardware = row
    next_status = None

    if role == "Manager" and status == "PENDING_MANAGER":
        if hardware == "Premium":
            next_status = "PENDING_FINANCE" 
        else:
            next_status ="PENDING_IT"

    elif role == "Finance" and status == "PENDING_FINANCE":
        next_status = "PENDING_IT"

    elif role == "IT" and status == "PENDING_IT":
        next_status = "COMPLETED"

    else:
        c.close()
        conn.close()
        raise HTTPException(status_code=403)
    
    c.execute("UPDATE tickets SET status = %s WHERE id = %s", (next_status, ticket_id))
    c.execute("""
        INSERT INTO history (ticket_id, user_id, stage, created_at)
        VALUES (%s, %s, %s, %s)
    """, (ticket_id, user_id, f"APPROVE {next_status}", datetime.now().isoformat()))

    conn.commit()
    c.close()
    conn.close()

    return {"new_status": next_status}


@app.post("/tickets/{ticket_id}/reject")
def reject_ticket(ticket_id: int, authorization: str = Header(None)):
    user_data = verify_token(authorization)
    user_id = user_data["user_id"]
    role = user_data["role"]
    
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT status FROM tickets WHERE id = %s", (ticket_id,))
    row = c.fetchone()

    if not row:
        c.close()
        conn.close()
        raise HTTPException(status_code=404, detail="nu exista tichetul")
    
    status = row[0]
    if status not in ["PENDING_MANAGER", "PENDING_FINANCE", "PENDING_IT"]:
        c.close()
        conn.close()
        raise HTTPException(status_code=403, detail="acest rol nu poate respinge tichetul")
    
    c.execute("UPDATE tickets SET status = 'Needs Rework' WHERE id = %s", (ticket_id,))

    c.execute("""
        INSERT INTO history (ticket_id, user_id, stage, created_at)
        VALUES (%s, %s, %s, %s)
    """, (ticket_id, user_id, f"Needs Rework", datetime.now().isoformat()))

    conn.commit()
    c.close()
    conn.close()

    return {"new_status": "Needs Rework", "message": "tichet respins, trimis la HR"}


@app.put("/tickets/{ticket_id}")
def edit_ticket(ticket_id: int, ticket: TicketEdit, authorization: str = Header(None)):
    user_data = verify_token(authorization)

    if user_data["role"] != "HR":
        raise HTTPException(status_code=403, detail="doar HR poate edita tichete")
    
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT status FROM tickets WHERE id = %s", (ticket_id,))
    row = c.fetchone()

    if not row:
        c.close()
        conn.close()
        raise HTTPException(status_code=404, detail="nu exista tichetul")

    if row[0] != "Needs Rework":
        c.close()
        conn.close()
        raise HTTPException(status_code=403, detail="tichetul nu poate fi editat")
    
    c.execute("""
        UPDATE tickets
        SET employee_name = %s, role = %s, start_date = %s, hardware = %s, status = 'PENDING_MANAGER'
        WHERE id = %s
    """, (ticket.employee_name, ticket.role, ticket.start_date, ticket.hardware, ticket_id))
 
    c.execute("""
        INSERT INTO history (ticket_id, user_id, stage, created_at)
        VALUES (%s, %s, %s, %s)
    """, (ticket_id, user_data["user_id"], "EDIT -> PENDING_MANAGER (restart workflow)", datetime.now().isoformat()))
 
    conn.commit()
    c.close()
    conn.close()
 
    return {"new_status": "PENDING_MANAGER", "message": "tichet actualizat de HR"}
 