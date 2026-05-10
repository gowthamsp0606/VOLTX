# Contributing to VOLTX

Thank you for your interest in VOLTX. This is an early-stage startup project
built for the Frontier Hackathon. Contributions, feedback, and ideas are welcome.

## Ways to Contribute

### 1. Report Issues
Found a bug or have a suggestion? Open a GitHub issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behaviour
- Your environment (OS, Python version, ESP32 board)

### 2. Improve the ML Model
The Isolation Forest model is trained on synthetic data. If you have access to
real electricity consumption datasets, contributions to improve detection
accuracy are highly valuable.

- Dataset format: CSV with columns `voltage`, `current`, `label` (1=normal, -1=theft)
- Place training scripts in `/model/` directory
- Document false positive rate on your test set

### 3. Add New Community Features
Current priority features:
- [ ] Reputation scoring per house
- [ ] Minimum uptime threshold for community bonus eligibility
- [ ] Multi-admin community governance
- [ ] DT-level feeder loss aggregation dashboard

### 4. Improve Smart Contract
The Anchor contract is deployed on devnet. Priority improvements:
- [ ] On-chain community registry (currently off-chain in communities.json)
- [ ] Escrow-based reward holding before field verification
- [ ] Governance voting for community admin changes

## Development Setup

```bash
# Clone
git clone https://github.com/gowthamsp0606/VOLTX.git
cd VOLTX

# Python backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Smart contract
cd contract
anchor build
anchor test
```

## Pull Request Guidelines

1. Fork the repo and create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes with clear commit messages
3. Test your changes locally
4. Open a PR with a description of what you changed and why

## Contact

For partnership, pilot deployment, or EB integration enquiries:
Open a GitHub issue tagged `[partnership]` or reach out via the hackathon submission.
