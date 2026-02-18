import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

state = {
    "market": {
        "occupancy": 0.95,
        "rent_price": 50,
        "interest_rate": 0.05,
    },
    "wallets": {
        "treasury": 5000.0,
        "covenant": 0.0,
        "data": 0.0
    },
    "status": {
        "safe_mode": False,
        "dscr": 1.5,
        "last_check": "Never"
    },
    "logs": []
}

class MarketUpdate(BaseModel):
    occupancy: float
    rent_price: float
    interest_rate: float

def add_log(agent: str, message: str, type: str = "info"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        "id": len(state["logs"]) + 1,
        "time": timestamp,
        "agent": agent,
        "message": message,
        "type": type
    }
    state["logs"] = [log_entry] + state["logs"][:49]

def process_payment(sender: str, receiver: str, amount: float, purpose: str):
    if state["wallets"][sender] >= amount:
        state["wallets"][sender] -= amount
        state["wallets"][receiver] += amount
        add_log(sender, f"Paid ${amount} to {receiver} for {purpose}", "payment")
        return True
    else:
        add_log(sender, f"PAYMENT FAILED: Insufficient funds to pay {receiver}", "danger")
        return False

async def run_agent_loop():
    print("Agent Loop Started...")
    while True:
        try:
            current_occupancy = state["market"]["occupancy"]
            current_rate = state["market"]["interest_rate"]
            
            data_fee = 0.01
            if process_payment("treasury", "data", data_fee, "Market Data Feed"):
                pass 
            
            risk_fee = 0.05 if current_occupancy > 0.8 else 0.50 
            
            if process_payment("treasury", "covenant", risk_fee, "DSCR Health Check"):
                net_operating_income = current_occupancy * 100 * 0.5 
                debt_service = 40 * (1 + current_rate)
                
                dscr = round(net_operating_income / debt_service, 2)
                state["status"]["dscr"] = dscr
                state["status"]["last_check"] = datetime.now().strftime("%H:%M:%S")

                if dscr < 1.10:
                    if not state["status"]["safe_mode"]:
                        state["status"]["safe_mode"] = True
                        add_log("Covenant", f"CRITICAL: DSCR {dscr} < 1.10. TRIGGERING SAFE MODE!", "danger")
                        add_log("Treasury", "LOCKING ON-CHAIN CONTRACT: Distributions Frozen.", "alert")
                else:
                    if state["status"]["safe_mode"]:
                        state["status"]["safe_mode"] = False
                        add_log("Covenant", f"Recovery Detected: DSCR {dscr}. Resuming operations.", "success")
                        add_log("Treasury", "UNLOCKING CONTRACT: Distributions Resumed.", "info")

        except Exception as e:
            print(f"Error in loop: {e}")
            
        await asyncio.sleep(3)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(run_agent_loop())

@app.get("/")
def read_root():
    return {"status": "CRE Agent Mesh Online"}

@app.get("/state")
def get_state():
    return state

@app.post("/admin/update-market")
def update_market(update: MarketUpdate):
    state["market"]["occupancy"] = update.occupancy
    state["market"]["rent_price"] = update.rent_price
    state["market"]["interest_rate"] = update.interest_rate
    
    add_log("Admin", f"MARKET SHOCK: Occupancy set to {int(update.occupancy*100)}%", "alert")
    return {"status": "Market Updated"}

@app.post("/admin/reset")
def reset_simulation():
    state["market"]["occupancy"] = 0.95
    state["market"]["rent_price"] = 50
    state["market"]["interest_rate"] = 0.05
    state["status"]["safe_mode"] = False
    state["wallets"]["treasury"] = 5000.0
    add_log("Admin", "Simulation Reset to Default", "info")
    return {"status": "Reset"}