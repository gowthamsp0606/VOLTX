# get_pda.py
from solders.pubkey import Pubkey
from solders.keypair import Keypair
import json

PROGRAM_ID = Pubkey.from_string("2Ru7HMxTjdZkVyRgQN3ygZSXh6Zdx62y2kryqwTQn24k")

# Load your admin wallet
with open("admin.json") as f:
    secret = json.load(f)
ADMIN = Keypair.from_bytes(bytes(secret))

# Derive PDA using seeds = [b"state", admin_pubkey]
pda, bump = Pubkey.find_program_address(
    [b"state", bytes(ADMIN.pubkey())],
    PROGRAM_ID
)

print("PROGRAM_ID    :", PROGRAM_ID)
print("ADMIN WALLET  :", ADMIN.pubkey())
print("STATE_ACCOUNT :", pda)
print("BUMP          :", bump)