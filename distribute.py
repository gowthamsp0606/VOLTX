import subprocess
import sys
import os

# Update these paths to the full location of your keypair files
MINT = "6VLPugbYj1GiYcYeQGzTRHh6aNxs5Lz3chd3X7x5wxwB"
POOL_OWNER = "/home/samverth/token-2022/keys/reward-pool.json"
FEE_PAYER = "/home/samverth/.config/solana/devnet.json"

def run_cmd(cmd):
    """Run a CLI command and return stdout or raise error."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    else:
        raise Exception(result.stderr)

def distribute(recipient_pubkey, amount):
    # Resolve reward pool ATA
    reward_pool_auth = run_cmd(["solana-keygen", "pubkey", POOL_OWNER])
    reward_pool_ata = run_cmd([
        "spl-token", "address", "--verbose",
        "--token", MINT, "--owner", reward_pool_auth, "--program-2022"
    ]).split()[-1]

    # Resolve recipient ATA
    recipient_ata = run_cmd([
        "spl-token", "address", "--verbose",
        "--token", MINT, "--owner", recipient_pubkey, "--program-2022"
    ]).split()[-1]

    # Transfer
    print(f"Transferring {amount} tokens to {recipient_ata}...")
    transfer_out = run_cmd([
        "spl-token", "transfer",
        "--owner", POOL_OWNER,
        "--fee-payer", FEE_PAYER,
        "--program-2022",
        MINT, str(amount), recipient_ata,
        "--from", reward_pool_ata
    ])
    print(transfer_out)

    # Verify balances
    print(run_cmd(["spl-token", "display", recipient_ata, "--program-2022"]))
    print(run_cmd(["spl-token", "display", reward_pool_ata, "--program-2022"]))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 distribute.py <recipient_pubkey> <amount>")
        sys.exit(1)

    recipient = sys.argv[1]
    amount = int(sys.argv[2])
    distribute(recipient, amount)
