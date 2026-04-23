import json
import hashlib
import struct
import joblib
import numpy as np
from datetime import datetime
from typing import Optional, Dict, List
 
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
 
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.transaction import Transaction
from solders.message import Message
from solders.instruction import Instruction, AccountMeta
 
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TxOpts
 
 
# -------------------------------------------------
# FASTAPI SETUP
# -------------------------------------------------
 
app = FastAPI(title="VOLTX Community Theft Monitor")
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
 
# -------------------------------------------------
# LOAD AI MODEL
# -------------------------------------------------
 
model = joblib.load("theft_model.pkl")
scaler = joblib.load("scaler.pkl")
 
 
# -------------------------------------------------
# SOLANA CONFIG
# -------------------------------------------------
 
RPC_URL = "https://api.devnet.solana.com"
 
PROGRAM_ID = Pubkey.from_string(
    "2Ru7HMxTjdZkVyRgQN3ygZSXh6Zdx62y2kryqwTQn24k"
)
 
STATE_ACCOUNT = Pubkey.from_string(
    "4zjbEDTvKoh2GdYAQoEYWAQRMvGzkm491t2iM6q4VSUj"
)
 
REWARD_POOL = Pubkey.from_string(
    "2PL9XnPPhQb9G2kbh9UMpKeJgkhfKkLCpeCRyKg3BC44"
)
 
TOKEN_PROGRAM = Pubkey.from_string(
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
)
 
 
# -------------------------------------------------
# REWARD SPLIT CONFIG
# -------------------------------------------------
 
INDIVIDUAL_SHARE  = 0.60   # 60% to the house that detected theft
COMMUNITY_SHARE   = 0.40   # 40% split equally among all other community members
 
# Base reward: 1000 tokens at 100% confidence (scaled linearly by confidence)
# Token has 9 decimals (same as SOL), so multiply by 1_000_000_000
BASE_REWARD_TOKENS = 1_000
 
 
# -------------------------------------------------
# COMMUNITY REGISTRY
# -------------------------------------------------
# Structure:
#   COMMUNITIES = {
#       "community_id": {
#           "house_id": "SolanaTokenAccountAddress",
#           ...
#       }
#   }
# In production: replace with a database.
 
def load_communities() -> Dict[str, Dict[str, str]]:
    try:
        with open("communities.json") as f:
            return json.load(f)
    except FileNotFoundError:
        # Seed with one demo community containing one house
        default = {
            "greenwood": {
                "house_a": "4c2foTvPqNBu9RSqYKEkZTQXLzD2xaELjeNKb3bHgriH",
            }
        }
        with open("communities.json", "w") as f:
            json.dump(default, f, indent=2)
        return default
 
def save_communities():
    with open("communities.json", "w") as f:
        json.dump(COMMUNITIES, f, indent=2)
 
COMMUNITIES: Dict[str, Dict[str, str]] = load_communities()
 
 
# -------------------------------------------------
# ADMIN WALLET
# -------------------------------------------------
 
with open("admin_new.json") as f:
    secret = json.load(f)
 
ADMIN = Keypair.from_bytes(bytes(secret))
print("ADMIN WALLET:", ADMIN.pubkey())
 
 
# -------------------------------------------------
# IN-MEMORY STORAGE
# -------------------------------------------------
 
history: List[dict] = []
latest_status: Dict[str, dict] = {}   # keyed by house_id
 
 
# -------------------------------------------------
# ANCHOR DISCRIMINATOR
# -------------------------------------------------
 
def anchor_discriminator(name: str) -> bytes:
    return hashlib.sha256(f"global:{name}".encode()).digest()[:8]
 
REWARD_COMMUNITY_DISCRIMINATOR = anchor_discriminator("reward_community")
 
 
# -------------------------------------------------
# REWARD CALCULATION
# -------------------------------------------------
 
def calculate_rewards(confidence: int, other_member_count: int):
    """
    Returns (individual_amount, bonus_per_member) in raw token units (9 decimals).
 
    confidence         : 0-100 integer
    other_member_count : number of community members EXCLUDING the reporter
    """
    total = int((confidence / 100) * BASE_REWARD_TOKENS * 1_000_000_000)
 
    individual      = int(total * INDIVIDUAL_SHARE)
    community_pool  = int(total * COMMUNITY_SHARE)
    bonus_per_member = (
        community_pool // other_member_count if other_member_count > 0 else 0
    )
 
    return individual, bonus_per_member
 
 
# -------------------------------------------------
# SOLANA — SEND COMMUNITY REWARD TRANSACTION
# -------------------------------------------------
 
async def reward_community_onchain(
    reporter_token_account: Pubkey,
    community_member_accounts: List[Pubkey],
    voltage: int,
    current: int,
    confidence: int,
) -> Optional[str]:
    """
    Sends ONE Solana transaction that:
      1. Transfers individual_amount (60%) → reporter's token account
      2. Transfers bonus_per_member (40% / N) → each other community member
    The Rust program receives member_count so it can loop over remaining_accounts.
    """
    try:
        async with AsyncClient(RPC_URL) as client:
 
            individual_amount, bonus_per_member = calculate_rewards(
                confidence, len(community_member_accounts)
            )
 
            # Core fixed accounts
            accounts = [
                AccountMeta(STATE_ACCOUNT,           False, True),
                AccountMeta(ADMIN.pubkey(),           True,  True),
                AccountMeta(REWARD_POOL,              False, True),
                AccountMeta(reporter_token_account,   False, True),  # index 3 = reporter
                AccountMeta(TOKEN_PROGRAM,            False, False),
            ]
 
            # Remaining accounts = other community members (writable, non-signer)
            for member_pubkey in community_member_accounts:
                accounts.append(AccountMeta(member_pubkey, False, True))
 
            # Instruction data layout (all u64 little-endian):
            # [discriminator 8B][voltage][current][confidence]
            # [individual_amount][bonus_per_member][member_count][_reserved]
            instruction_data = (
                REWARD_COMMUNITY_DISCRIMINATOR +
                struct.pack(
                    "<QQQQQQQ",
                    voltage,
                    current,
                    confidence,
                    individual_amount,
                    bonus_per_member,
                    len(community_member_accounts),
                    0,  # reserved for future use
                )
            )
 
            instruction = Instruction(PROGRAM_ID, instruction_data, accounts)
 
            latest   = await client.get_latest_blockhash()
            blockhash = latest.value.blockhash
 
            message = Message.new_with_blockhash(
                [instruction], ADMIN.pubkey(), blockhash
            )
            tx = Transaction([ADMIN], message, blockhash)
 
            result    = await client.send_transaction(tx, opts=TxOpts(skip_preflight=False))
            signature = str(result.value)
 
            print(f"✅ COMMUNITY REWARD TX: {signature}")
            print(f"   Reporter  → {individual_amount / 1e9:.4f} tokens")
            print(f"   Each peer → {bonus_per_member  / 1e9:.4f} tokens  ({len(community_member_accounts)} peers)")
 
            return signature
 
    except Exception as e:
        print(f"❌ ONCHAIN ERROR: {e}")
        return None
 
 
# -------------------------------------------------
# PYDANTIC MODELS
# -------------------------------------------------
 
class PredictRequest(BaseModel):
    voltage:      float
    current:      float
    house_id:     str
    community_id: str
 
class RegisterRequest(BaseModel):
    community_id:  str
    house_id:      str
    token_account: str   # Solana SPL token account address
 
class CreateCommunityRequest(BaseModel):
    community_id:        str
    admin_house_id:      str
    admin_token_account: str
 
 
# -------------------------------------------------
# COMMUNITY MANAGEMENT ENDPOINTS
# -------------------------------------------------
 
@app.post("/community/create")
async def create_community(req: CreateCommunityRequest):
    """Create a new community. The first house is the admin/founder."""
    if req.community_id in COMMUNITIES:
        raise HTTPException(400, "Community already exists")
 
    try:
        Pubkey.from_string(req.admin_token_account)
    except Exception:
        raise HTTPException(400, "Invalid Solana token account address")
 
    COMMUNITIES[req.community_id] = {req.admin_house_id: req.admin_token_account}
    save_communities()
 
    return {
        "success": True,
        "community_id": req.community_id,
        "message": f"Community '{req.community_id}' created. House '{req.admin_house_id}' is the founder.",
    }
 
 
@app.post("/community/register")
async def register_house(req: RegisterRequest):
    """Register a new house into an existing community."""
    if req.community_id not in COMMUNITIES:
        raise HTTPException(404, "Community not found")
 
    if req.house_id in COMMUNITIES[req.community_id]:
        raise HTTPException(400, "House ID already registered in this community")
 
    try:
        Pubkey.from_string(req.token_account)
    except Exception:
        raise HTTPException(400, "Invalid Solana token account address")
 
    COMMUNITIES[req.community_id][req.house_id] = req.token_account
    save_communities()
 
    return {
        "success":       True,
        "house_id":      req.house_id,
        "community_id":  req.community_id,
        "total_members": len(COMMUNITIES[req.community_id]),
        "message":       f"House '{req.house_id}' joined '{req.community_id}'",
    }
 
 
@app.get("/community/{community_id}")
async def get_community(community_id: str):
    if community_id not in COMMUNITIES:
        raise HTTPException(404, "Community not found")
 
    members = COMMUNITIES[community_id]
    return {
        "community_id":   community_id,
        "member_count":   len(members),
        "members":        list(members.keys()),
        "reward_split": {
            "reporter":        f"{int(INDIVIDUAL_SHARE * 100)}%",
            "community_bonus": f"{int(COMMUNITY_SHARE  * 100)}%",
        },
    }
 
 
@app.get("/communities")
async def list_communities():
    return {
        "communities": [
            {"id": cid, "member_count": len(m), "members": list(m.keys())}
            for cid, m in COMMUNITIES.items()
        ]
    }
 
 
# -------------------------------------------------
# CORE PREDICTION ENDPOINT  (called by ESP32)
# -------------------------------------------------
 
@app.post("/predict")
async def predict(data: PredictRequest):
    """
    Main endpoint hit by each ESP32 sensor node.
 
    Flow:
      1. Validate community + house membership
      2. Run Isolation Forest model
      3. If theft detected:
           a. Compute 60/40 reward split
           b. Send single Solana transaction rewarding reporter + all peers
      4. Return full result with reward breakdown
    """
 
    # --- Validate ---
    if data.community_id not in COMMUNITIES:
        raise HTTPException(404, f"Community '{data.community_id}' not found. Register first via POST /community/create")
 
    community = COMMUNITIES[data.community_id]
 
    if data.house_id not in community:
        raise HTTPException(403, f"House '{data.house_id}' is not registered in '{data.community_id}'. Use POST /community/register")
 
    # --- ML inference ---
    X = np.array([[data.voltage, data.current]])
    X_scaled   = scaler.transform(X)
    prediction = int(model.predict(X_scaled)[0])
    theft      = prediction == -1
    confidence = min(int(abs(model.decision_function(X_scaled)[0]) * 100), 100)
 
    tx = None
    reward_info = None
 
    if theft and confidence >= 10:
        print(f"\n⚡ THEFT DETECTED  house={data.house_id}  community={data.community_id}  confidence={confidence}%")
 
        reporter_pubkey = Pubkey.from_string(community[data.house_id])
 
        other_members = [
            Pubkey.from_string(addr)
            for hid, addr in community.items()
            if hid != data.house_id
        ]
        other_house_ids = [hid for hid in community if hid != data.house_id]
 
        individual_amount, bonus_per_member = calculate_rewards(confidence, len(other_members))
 
        tx = await reward_community_onchain(
            reporter_token_account    = reporter_pubkey,
            community_member_accounts = other_members,
            voltage    = int(data.voltage),
            current    = int(data.current),
            confidence = confidence,
        )
 
        reward_info = {
            "reporter_reward_tokens":     round(individual_amount  / 1e9, 4),
            "bonus_per_member_tokens":    round(bonus_per_member   / 1e9, 4),
            "community_members_rewarded": other_house_ids,
            "split": f"{int(INDIVIDUAL_SHARE*100)}/{int(COMMUNITY_SHARE*100)}",
        }
 
    result = {
        "timestamp":    datetime.utcnow().isoformat() + "Z",
        "house_id":     data.house_id,
        "community_id": data.community_id,
        "voltage":      data.voltage,
        "current":      data.current,
        "theft":        theft,
        "confidence":   confidence,
        "tx":           tx,
        "rewards":      reward_info,
    }
 
    latest_status[data.house_id] = result
    history.append(result)
 
    return result
 
 
# -------------------------------------------------
# STATUS & HISTORY ENDPOINTS
# -------------------------------------------------
 
@app.get("/status")
async def status():
    """Latest reading from every house across all communities."""
    return latest_status
 
@app.get("/status/{house_id}")
async def status_house(house_id: str):
    if house_id not in latest_status:
        raise HTTPException(404, "No data yet for this house")
    return latest_status[house_id]
 
@app.get("/history")
async def history_all(limit: int = 50):
    return history[-limit:]
 
@app.get("/history/{community_id}")
async def history_community(community_id: str, limit: int = 50):
    return [h for h in history if h.get("community_id") == community_id][-limit:]
 
@app.get("/history/{community_id}/{house_id}")
async def history_house(community_id: str, house_id: str, limit: int = 50):
    return [
        h for h in history
        if h.get("community_id") == community_id and h.get("house_id") == house_id
    ][-limit:]
 
@app.get("/health")
async def health():
    return {
        "status":      "ok",
        "communities": len(COMMUNITIES),
        "total_houses": sum(len(m) for m in COMMUNITIES.values()),
    }