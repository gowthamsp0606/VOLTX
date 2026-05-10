# VOLTX — Decentralized Electricity Theft Detection Network

<div align="center">

![VOLTX Banner](https://img.shields.io/badge/VOLTX-Community%20Security%20Network-7F77DD?style=for-the-badge)
![Solana](https://img.shields.io/badge/Solana-Devnet-9945FF?style=for-the-badge&logo=solana)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi)
![ESP32](https://img.shields.io/badge/ESP32-Hardware-E7352C?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A community-powered IoT system that detects electricity theft in real time and rewards honest households with VOLTX tokens on the Solana blockchain.**

[Live Demo](#demo) · [Architecture](#architecture) · [Quick Start](#quick-start) · [Hardware Setup](#hardware-setup) · [Smart Contract](#smart-contract)

</div>

---

## The Problem

Electricity theft costs India **₹30,000 crore every year** — and Tamil Nadu alone loses over **₹4,000 crore annually**. Honest households pay inflated bills to subsidise their neighbours' theft. Utility linemen detect theft manually, once a month, creating massive gaps in enforcement.

Existing smart meter solutions detect tampering at the meter — but miss feeder-level hook connections, don't incentivise community participation, and create no tamper-proof legal evidence.

**VOLTX fixes this.**

---

## What VOLTX Does

VOLTX turns every household in a community into an active node in a decentralized theft detection network:

1. **ESP32 sensors** measure voltage and current at each house and at the distribution transformer level
2. **Isolation Forest ML model** detects theft signatures in real time
3. **Community reward logic** pays the reporting house 60% and splits 40% among all neighbours
4. **Solana smart contract** executes all payments in a single tamper-proof transaction
5. **Field team verification** approves each detection before any reward is released — zero false payouts

Every detection creates a **permanent on-chain record** that is mathematically impossible to tamper with — legally admissible evidence that no centralised system can provide.

---

## Demo

### Live Transaction on Solana Devnet
```
Signature: 5oBqncgT13s9ZAicXwE2iapnAjZBjYPHe7emuUHKEF35gAvVoLxPK7BrvNvwoD6y7Y9pZKxPCWfLdoxbGBttoHeg
```
[View on Solana Explorer →](https://explorer.solana.com/tx/5oBqncgT13s9ZAicXwE2iapnAjZBjYPHe7emuUHKEF35gAvVoLxPK7BrvNvwoD6y7Y9pZKxPCWfLdoxbGBttoHeg?cluster=devnet)

This transaction shows **3 simultaneous token transfers** in one block — 66 tokens to the reporter, 22 tokens each to two community peers. The community reward split working exactly as designed.

### Demo Flow
```
ESP32 detects anomaly → ML confirms theft → Alert created
        ↓
Field team dispatched → Physical verification
        ↓
Approval triggers Solana transaction
        ↓
Reporter gets 60% · Community shares 40%
        ↓
Permanent record on Solana · Verify on Solscan
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GREENWOOD COMMUNITY                       │
│                                                             │
│  [House A]      [House B]      [House C]      [DT Sensor]  │
│  ESP32+ACS712   ESP32+ACS712   ESP32+ACS712   ESP32+ACS712  │
│      │               │               │               │      │
└──────┴───────────────┴───────────────┴───────────────┴──────┘
                        │
                        ▼
              ┌─────────────────┐
              │   FastAPI       │
              │   Backend       │
              │                 │
              │ • Isolation     │
              │   Forest ML     │
              │ • Community     │
              │   registry      │
              │ • Alert mgmt    │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Solana Smart   │
              │  Contract       │
              │                 │
              │ • reward_       │
              │   community()   │
              │ • 60/40 split   │
              │ • On-chain      │
              │   events        │
              └─────────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Hardware | ESP32, ACS712 current sensor, 12V battery |
| ML Model | Isolation Forest (scikit-learn) |
| Backend | FastAPI (Python) |
| Blockchain | Solana (Anchor framework, Rust) |
| Token | VOLTX SPL token (1,000,000 supply) |
| Network | Solana Devnet |

---

## Token Economics

### VOLTX Token — 1,000,000 Total Supply

| Allocation | % | Tokens | Purpose |
|------------|---|--------|---------|
| Reward Pool | 40% | 400,000 | Funded by government / utilities |
| Team & Operations | 20% | 200,000 | 2-year vest |
| Ecosystem Growth | 20% | 200,000 | Utility partnerships |
| Reserve | 15% | 150,000 | Pool top-ups |
| Early Adopters | 5% | 50,000 | Beta pilot households |

### Per Detection Reward

| Recipient | Share | VOLTX (at 100% confidence) |
|-----------|-------|--------------------------|
| Reporter (detecting house) | 60% | 600 VOLTX |
| Each community peer | 40% ÷ N | 100–200 VOLTX |

Rewards scale linearly with ML confidence score. A 70% confidence detection pays 700 total VOLTX.

### Utility Floor Value
VOLTX can be redeemed for electricity bill discounts at partner utilities at a fixed ₹5/token rate — giving it inherent utility value independent of market price.

---

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+ (for Anchor CLI)
- Rust + Solana CLI
- Anchor CLI 0.29.0

### 1. Clone the Repository
```bash
git clone https://github.com/gowthamsp0606/VOLTX.git
cd VOLTX
```

### 2. Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn solders solana joblib numpy pydantic

# Place your trained model files in the root directory
# theft_model.pkl — trained Isolation Forest
# scaler.pkl      — fitted StandardScaler
# admin.json      — Solana admin keypair (array of 64 bytes)

# Run the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Deploy Smart Contract
```bash
cd contract

# Install dependencies
anchor build

# Deploy to devnet
anchor deploy --provider.cluster devnet

# Copy the new program ID into main.py and lib.rs
```

### 4. Create a Community
```bash
curl -X POST http://localhost:8000/community/create \
  -H "Content-Type: application/json" \
  -d '{
    "community_id": "greenwood",
    "admin_house_id": "house_a",
    "admin_token_account": "YOUR_SOLANA_TOKEN_ACCOUNT"
  }'
```

### 5. Register Houses
```bash
# Register house_b
curl -X POST http://localhost:8000/community/register \
  -H "Content-Type: application/json" \
  -d '{
    "community_id": "greenwood",
    "house_id": "house_b",
    "token_account": "HOUSE_B_TOKEN_ACCOUNT"
  }'

# Register house_c
curl -X POST http://localhost:8000/community/register \
  -H "Content-Type: application/json" \
  -d '{
    "community_id": "greenwood",
    "house_id": "house_c",
    "token_account": "HOUSE_C_TOKEN_ACCOUNT"
  }'
```

### 6. Flash ESP32
Open `esp32/voltx_real_sensor.ino` in Arduino IDE. Update:
```cpp
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* SERVER_URL    = "http://YOUR_SERVER_IP:8000/predict";
```
Flash and monitor serial output.

---

## Hardware Setup

### Components Required

| Component | Spec | Qty | Price |
|-----------|------|-----|-------|
| ESP32 dev board | 38-pin | 1 | ₹500 |
| ACS712 current sensor | 5A module | 4 | ₹400 |
| 12V sealed lead acid battery | 7Ah | 1 | ₹400 |
| LM7805 voltage regulator | 5V 1.5A | 1 | ₹20 |
| 12V LED bulbs | Any wattage | 3 | ₹150 |
| 100μF capacitor | 25V | 2 | ₹10 |
| Alligator clip | — | 2 | ₹30 |
| Breadboard | Full size | 1 | ₹80 |
| Jumper wires | M-M and M-F | 1 set | ₹80 |
| Cardboard + craft supplies | — | — | ₹100 |
| **Total** | | | **₹1,770** |

### Wiring

```
12V Battery (+)
      │
      ├──→ LM7805 (IN) → LM7805 (OUT) → 5V → ESP32 VIN
      │                                     → ACS712 VCC (×4)
      │
      ├──→ ACS712 DT (GPIO34) ← Main line current
      │
      ├──→ House A branch → ACS712-A (GPIO35) → LED-A
      ├──→ House B branch → ACS712-B (GPIO32) → LED-B
      └──→ House C branch → ACS712-C (GPIO33) → LED-C

12V Battery (−) → Common ground for all components

Hook connection: alligator clip on main positive line
→ extra load draws current DT sees but no house measures
→ difference > 200mA = THEFT DETECTED
```

### Sensor Pin Map

| Sensor | GPIO | Measures |
|--------|------|---------|
| ACS712 #1 | 34 | DT level — total current |
| ACS712 #2 | 35 | House A current |
| ACS712 #3 | 32 | House B current |
| ACS712 #4 | 33 | House C current |

---

## API Reference

### Community Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/community/create` | POST | Create a new community |
| `/community/register` | POST | Register a house to a community |
| `/community/{id}` | GET | Get community info and members |
| `/communities` | GET | List all communities |
| `/community/{id}/uptime` | GET | House uptime status |
| `/community/{id}/stats` | GET | Detection stats and totals |

### Detection & Rewards

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/predict` | POST | ESP32 sends reading, triggers detection |
| `/alerts/pending` | GET | Alerts awaiting field verification |
| `/alerts/verify` | POST | Approve or reject a pending alert |
| `/alerts/history` | GET | All past alerts |
| `/dt/reading` | POST | DT-level feeder theft detection |

### Status & History

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/status` | GET | Latest reading from every house |
| `/status/{house_id}` | GET | Latest reading from one house |
| `/history` | GET | Full detection history |
| `/history/{community_id}` | GET | History filtered by community |
| `/health` | GET | Server health check |

### Example — Send a Reading (ESP32 payload)
```json
POST /predict
{
  "voltage": 11.8,
  "current": 3.2,
  "house_id": "house_a",
  "community_id": "greenwood"
}
```

### Example — Approve a Theft Alert
```json
POST /alerts/verify
{
  "alert_id": "A3F7B2",
  "approved": true,
  "notes": "Hook connection confirmed on feeder line"
}
```

---

## Smart Contract

### Program ID
```
2Ru7HMxTjdZkVyRgQN3ygZSXh6Zdx62y2kryqwTQn24k
```

### Instructions

| Instruction | Description |
|-------------|-------------|
| `initialize` | Create global state account |
| `create_community` | Register a new community on-chain |
| `register_house` | Add a house to a community |
| `reward_community` | Execute reward split — 60% reporter + 40% peers |

### Reward Split Logic
```
Total reward = (confidence / 100) × 1000 × 10⁹ lamports

Reporter   → total × 0.60
Each peer  → (total × 0.40) ÷ peer_count

All transfers in ONE Solana transaction
```

### On-Chain Event (emitted on every detection)
```rust
pub struct TheftRewardEvent {
    pub reporter:          Pubkey,
    pub community_members: u64,
    pub voltage:           u64,
    pub current:           u64,
    pub confidence:        u64,
    pub individual_amount: u64,
    pub bonus_per_member:  u64,
    pub total_paid:        u64,
    pub timestamp:         i64,
}
```

---

## How Sybil Resistance Works

VOLTX uses **physical installation as the sybil resistance mechanism** — stronger than any on-chain staking solution:

1. Every sensor is physically installed by a VOLTX field team member
2. The hardware device ID (MAC address) is registered at installation time
3. There is no remote signup — no wallet connect, no app registration
4. If there is no ESP32 on your meter installed by our team, you are not in the network

This maps directly to the startup model: every new community requires a field team visit, which creates a natural rate-limiting mechanism and builds EB relationships simultaneously.

---

## Why Blockchain?

Three reasons that are **impossible without blockchain**:

1. **Trustless reward distribution** — the utility cannot underpay or delay community rewards because the smart contract executes automatically with no human in the payment loop

2. **Tamper-proof evidence** — every detection is a Solana transaction hash. It cannot be edited, deleted, or fabricated — making it legally admissible in a way no centralised database ever could be

3. **Decentralised community incentives** — paying 20 households simultaneously in one transaction across a community takes 2 seconds on Solana for a fraction of a cent. No traditional payment rail can do that

---

## Business Model

### Revenue Streams
| Stream | Amount | Notes |
|--------|--------|-------|
| Utility subscription | ₹50,000/month per zone | Primary B2B revenue |
| Installation fee | ₹1,200 per household | Hardware + field team |
| Success fee | 20% of recovered revenue | Performance-based |

### Reward Pool Funding
The government funds the initial reward pool — India loses ₹30,000 crore yearly to electricity theft. Even a 10% reduction in one state justifies the investment many times over. As we scale, utility subscriptions continuously replenish the reward pool.

### Roadmap
```
Now (Hackathon)      → Household sensors + community rewards + on-chain proof
Month 1–3 (Pilot)   → DT sensor + feeder loss calc + TANGEDCO integration
Month 4–6 (Scale)   → Bill discount redemption + state-wide rollout
Year 1               → DEX listing + national expansion
```

---

## Project Structure

```
VOLTX/
├── main.py                    # FastAPI backend — core application
├── theft_model.pkl            # Trained Isolation Forest model
├── scaler.pkl                 # Fitted StandardScaler
├── communities.json           # Community registry (auto-created)
├── admin.json                 # Solana admin keypair
│
├── contract/
│   └── src/
│       └── lib.rs             # Anchor smart contract (Rust)
│
├── esp32/
│   ├── voltx_real_sensor.ino  # Real ACS712 sensor code
│   └── greenwood_all_houses.ino # Simulation code (3 houses, 1 ESP32)
│
└── README.md
```

---

## Deployed Contracts

| Network | Program ID |
|---------|-----------|
| Solana Devnet | `2Ru7HMxTjdZkVyRgQN3ygZSXh6Zdx62y2kryqwTQn24k` |
| State Account | `6qPJFRBxV6Th3swBecHJz1kEjoKtPcvdraxCRceZ56cd` |
| Reward Pool | `VkhWZeApX7qkzAMeQUT7DmkZf2TXv7BTkLmbLZu2njW` |

---

## Built For

- **Frontier Hackathon** — Colosseum × Solana global hackathon
- **Target accelerator** — Colosseum accelerator program ($250K funding)
- **Pilot region** — Erode, Tamil Nadu, India
- **Target utility** — TANGEDCO (Tamil Nadu Generation and Distribution Corporation)

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with hardware, ML, and Solana by **Gowtham S** from Erode, Tamil Nadu.

*"Electricity theft costs India ₹30,000 crore every year. VOLTX fixes that."*

</div>
