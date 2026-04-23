import json
import hashlib
import asyncio
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.transaction import Transaction
from solders.message import Message
from solders.instruction import Instruction, AccountMeta
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TxOpts

RPC_URL = "https://api.devnet.solana.com"
PROGRAM_ID = Pubkey.from_string("2Ru7HMxTjdZkVyRgQN3ygZSXh6Zdx62y2kryqwTQn24k")
SYSTEM_PROGRAM = Pubkey.from_string("11111111111111111111111111111111")

with open("admin_new.json") as f:
    secret = json.load(f)
ADMIN = Keypair.from_bytes(bytes(secret))
print("Admin:", ADMIN.pubkey())

STATE_PDA = Pubkey.from_string("4zjbEDTvKoh2GdYAQoEYWAQRMvGzkm491t2iM6q4VSUj")

def anchor_discriminator(name: str) -> bytes:
    return hashlib.sha256(f"global:{name}".encode()).digest()[:8]

async def main():
    async with AsyncClient(RPC_URL) as client:
        accounts = [
            AccountMeta(STATE_PDA,          False, True),
            AccountMeta(ADMIN.pubkey(),     True,  True),
            AccountMeta(SYSTEM_PROGRAM,     False, False),
        ]

        ix_data = anchor_discriminator("initialize")
        instruction = Instruction(PROGRAM_ID, ix_data, accounts)

        blockhash = (await client.get_latest_blockhash()).value.blockhash
        message = Message.new_with_blockhash([instruction], ADMIN.pubkey(), blockhash)
        tx = Transaction([ADMIN], message, blockhash)

        result = await client.send_transaction(tx, opts=TxOpts(skip_preflight=False))
        print("✅ Initialize TX:", result.value)

asyncio.run(main())