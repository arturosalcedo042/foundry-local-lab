import os
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg
from psycopg.rows import dict_row

app = FastAPI(title="Foundry-inspired local lab")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["GET", "PATCH"], allow_headers=["*"])

@contextmanager
def database():
    with psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row) as conn:
        yield conn

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/summary")
def summary():
    with database() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS orders, COALESCE(SUM(amount),0) AS revenue, COUNT(*) FILTER (WHERE status='pending') AS pending FROM orders")
            result = cur.fetchone()
            cur.execute("SELECT id, ran_at, customers_loaded, orders_loaded, result FROM pipeline_runs ORDER BY id DESC LIMIT 1")
            pipeline = cur.fetchone()
    return {"orders": result["orders"], "revenue": float(result["revenue"]), "pending": result["pending"], "pipeline": pipeline}

@app.get("/orders")
def orders():
    with database() as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT o.order_id, o.customer_id, c.name AS customer_name, c.region,
                       o.amount, o.status, o.payment_status
                       FROM orders o JOIN customers c USING (customer_id)
                       ORDER BY o.order_id LIMIT 500""")
            rows=cur.fetchall()
    return [{**r, "amount": float(r["amount"])} for r in rows]

class StatusUpdate(BaseModel):
    status: str

@app.patch("/orders/{order_id}/status")
def update_status(order_id: int, payload: StatusUpdate):
    allowed = {"pending", "shipped", "delivered", "cancelled"}
    if payload.status not in allowed:
        raise HTTPException(400, "Invalid status")
    with database() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE orders SET status = %s WHERE order_id = %s RETURNING order_id, status", (payload.status, order_id))
            updated = cur.fetchone()
            if updated is None:
                raise HTTPException(404, "Order not found")
    return updated
