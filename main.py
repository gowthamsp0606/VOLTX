import json
import hashlib
import struct
import joblib
import numpy as np

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

app = FastAPI()

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
    "8xjuMhJj32mJ6ATLVvPtPhdL3ZUPxVFLWkq3rXQJN5rB"
)

STATE_ACCOUNT = Pubkey.from_string(
    "FA6WX9X6BmBMUVD2a652KbJUQpJgmayFukv47FTNjLV9"
)

REWARD_POOL = Pubkey.from_string(
    "4fn3esYN7ijpLPQag7tKBAiFf56Kcn5nocS2u62RFtU6"
)

USER_TOKEN_ACCOUNT = Pubkey.from_string(
    "HkcqqFwTZBde1hzR4Yr1DoU9fyTNk7Ug3CNKtRa1E3b8"
)

TOKEN_PROGRAM = Pubkey.from_string(
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
)


# -------------------------------------------------
# ADMIN WALLET
# -------------------------------------------------

with open("admin.json") as f:
    secret = json.load(f)

ADMIN = Keypair.from_bytes(bytes(secret))

print("ADMIN WALLET:", ADMIN.pubkey())


# -------------------------------------------------
# STORAGE
# -------------------------------------------------

history = []
latest_status = {}


# -------------------------------------------------
# ANCHOR DISCRIMINATOR
# -------------------------------------------------

def anchor_discriminator(name: str):
    return hashlib.sha256(
        f"global:{name}".encode()
    ).digest()[:8]


REWARD_USER_DISCRIMINATOR = anchor_discriminator("reward_user")


# -------------------------------------------------
# SOLANA REWARD FUNCTION
# -------------------------------------------------

async def reward_user_onchain(voltage, current, confidence):

    try:

        async with AsyncClient(RPC_URL) as client:

            accounts = [

                AccountMeta(
                    STATE_ACCOUNT,
                    False,
                    True
                ),

                AccountMeta(
                    ADMIN.pubkey(),
                    True,
                    True
                ),

                AccountMeta(
                    REWARD_POOL,
                    False,
                    True
                ),

                AccountMeta(
                    USER_TOKEN_ACCOUNT,
                    False,
                    True
                ),

                AccountMeta(
                    TOKEN_PROGRAM,
                    False,
                    False
                ),
            ]

            # Pack Anchor instruction data
            instruction_data = (
                REWARD_USER_DISCRIMINATOR +
                struct.pack("<QQQ", voltage, current, confidence)
            )

            instruction = Instruction(
                PROGRAM_ID,
                instruction_data,
                accounts
            )

            latest = await client.get_latest_blockhash()
            blockhash = latest.value.blockhash

            message = Message.new_with_blockhash(
                [instruction],
                ADMIN.pubkey(),
                blockhash
            )

            tx = Transaction(
                [ADMIN],
                message,
                blockhash
            )

            result = await client.send_transaction(
                tx,
                opts=TxOpts(skip_preflight=False)
            )

            signature = result.value

            print("TOKEN REWARD SENT:", signature)

            return str(signature)

    except Exception as e:

        print("ONCHAIN ERROR:", e)

        return None


# -------------------------------------------------
# STATUS API
# -------------------------------------------------

@app.get("/status")
async def status():
    return latest_status


# -------------------------------------------------
# HISTORY API
# -------------------------------------------------

@app.get("/history")
async def history_api():
    return history[-50:]


# -------------------------------------------------
# ESP32 PREDICTION API
# -------------------------------------------------

@app.post("/predict")
async def predict(data: dict):

    voltage = float(data["voltage"])
    current = float(data["current"])

    X = np.array([[voltage, current]])

    X_scaled = scaler.transform(X)

    prediction = int(model.predict(X_scaled)[0])

    theft = bool(prediction == -1)

    confidence = int(
        abs(model.decision_function(X_scaled)[0]) * 100
    )

    tx = None

    if theft:

        print("⚠️ THEFT DETECTED")

        tx = await reward_user_onchain(
            int(voltage),
            int(current),
            int(confidence)
        )

    result = {

        "voltage": float(voltage),
        "current": float(current),
        "theft": bool(theft),
        "confidence": int(confidence),
        "tx": str(tx) if tx else None
    }

    latest_status.update(result)

    history.append(result)

    return result