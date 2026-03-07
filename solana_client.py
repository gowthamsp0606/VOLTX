import asyncio
import json
from anchorpy import Provider, Program, Wallet
from solana.rpc.async_api import AsyncClient
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.transaction import Transaction
from solana.rpc.commitment import Confirmed

# ---------- CONFIG ----------

PROGRAM_ID = PublicKey("8xjuMhJj32mJ6ATLVvPtPhdL3ZUPxVFLWkq3rXQJN5rB")
STATE_ACCOUNT = PublicKey("8Q5pZHg8H6HKu1Z1z7LAKtCL1wXNXKMNcn5S2VKmkncJ")

REWARD_POOL = PublicKey("4fn3esYN7ijpLPQag7tKBAiFf56Kcn5nocS2u62RFtU6")
USER_TOKEN = PublicKey("ECnBuCNAzAH35taQE1a6Exs6hGM3bCQwmv8xSwPrYsBs")

# Load admin wallet
with open("/home/solana/.config/solana/id.json") as f:
    secret = json.load(f)

admin_keypair = Keypair.from_secret_key(bytes(secret))
wallet = Wallet(admin_keypair)

# Load IDL
with open("voltguard_program.json") as f:
    idl = json.load(f)


async def reward_user_onchain(voltage, current, confidence):
    async with AsyncClient("https://api.devnet.solana.com") as client:
        provider = Provider(client, wallet)
        program = Program(idl, PROGRAM_ID, provider)

        tx = await program.rpc["reward_user"](
            voltage,
            current,
            confidence,
            ctx={
                "accounts": {
                    "state": STATE_ACCOUNT,
                    "admin": admin_keypair.public_key,
                    "reward_pool": REWARD_POOL,
                    "user_token": USER_TOKEN,
                    "token_program": PublicKey(
                        "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
                    ),
                }
            },
        )

        return tx