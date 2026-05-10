use anchor_lang::prelude::*;
use anchor_lang::solana_program::program::invoke;
use anchor_spl::token::{self, Token, TokenAccount, Transfer};
use spl_token::instruction as spl_instruction;

declare_id!("2Ru7HMxTjdZkVyRgQN3ygZSXh6Zdx62y2kryqwTQn24k");

// ─────────────────────────────────────────────────────────────
//  Constants
// ─────────────────────────────────────────────────────────────

/// Maximum houses allowed in a single community.
/// Solana transaction size limits how many remaining_accounts we can pass.
pub const MAX_COMMUNITY_SIZE: usize = 20;

/// Minimum confidence (0-100) required to trigger a reward.
pub const MIN_CONFIDENCE: u64 = 10;

// ─────────────────────────────────────────────────────────────
//  Program
// ─────────────────────────────────────────────────────────────

#[program]
pub mod electricity_theft_monitor {
    use super::*;

    // ── Initialize global state ───────────────────────────────

    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
        let state = &mut ctx.accounts.state;
        state.admin           = ctx.accounts.admin.key();
        state.total_rewards   = 0;
        state.detection_count = 0;
        state.community_count = 0;
        msg!("VOLTX state initialised. Admin: {}", state.admin);
        Ok(())
    }

    // ── Create a community ────────────────────────────────────
    /// Registers a new community on-chain with a unique ID (max 32 chars).
    /// The community PDA stores how many members are registered and total
    /// rewards distributed within the community.

    pub fn create_community(
        ctx: Context<CreateCommunity>,
        community_id: String,
    ) -> Result<()> {
        require!(community_id.len() <= 32, TheftError::CommunityIdTooLong);

        let community = &mut ctx.accounts.community;
        community.admin          = ctx.accounts.admin.key();
        community.community_id   = community_id.clone();
        community.member_count   = 0;
        community.total_rewards  = 0;
        community.detection_count = 0;

        let state = &mut ctx.accounts.state;
        state.community_count += 1;

        msg!("Community '{}' created.", community_id);
        Ok(())
    }

    // ── Register a house into a community ─────────────────────
    /// Creates a HouseMember PDA that links a house's token account to a community.
    /// Only the community admin can register members (prevents spam).

    pub fn register_house(
        ctx: Context<RegisterHouse>,
        community_id: String,
        house_id: String,
    ) -> Result<()> {
        require!(house_id.len() <= 32, TheftError::HouseIdTooLong);

        // Save keys before taking any mutable borrows
        let community_key        = ctx.accounts.community.key();
        let house_token_acct_key = ctx.accounts.house_token_account.key();

        {
            let community = &ctx.accounts.community;
            require!(
                community.member_count < MAX_COMMUNITY_SIZE as u64,
                TheftError::CommunityFull
            );
        }

        let member = &mut ctx.accounts.house_member;
        member.community       = community_key;
        member.house_id        = house_id.clone();
        member.token_account   = house_token_acct_key;
        member.total_received  = 0;
        member.detection_count = 0;
        member.joined_at       = Clock::get()?.unix_timestamp;

        let community = &mut ctx.accounts.community;
        community.member_count += 1;

        msg!(
            "House '{}' registered in community '{}'. Total members: {}",
            house_id, community_id, community.member_count
        );
        Ok(())
    }

    // ── Reward community (core instruction) ───────────────────
    /// Called by the backend when a theft is detected.
    ///
    /// Accounts (fixed):
    ///   0  state            – global state PDA (mut)
    ///   1  admin            – signer
    ///   2  reward_pool      – SPL token account holding reward tokens (mut)
    ///   3  reporter_account – token account of the reporting house (mut)
    ///   4  token_program
    ///
    /// remaining_accounts:
    ///   [5..5+member_count]  – token accounts of all OTHER community members (mut)
    ///
    /// Reward split:
    ///   • reporter  → individual_amount   (60% of total, pre-computed off-chain)
    ///   • each peer → bonus_per_member    (40% / N, pre-computed off-chain)
    ///
    /// The on-chain program trusts the amounts passed in BUT enforces:
    ///   • admin signer check
    ///   • confidence >= MIN_CONFIDENCE
    ///   • mint consistency (reward_pool.mint == reporter_account.mint)
    ///   • member_count == remaining_accounts.len()
    ///   • math overflow checks on all additions

    pub fn reward_community<'c>(
        ctx: Context<'_, '_, 'c, 'c, RewardCommunity<'c>>,
        voltage:           u64,
        current:           u64,
        confidence:        u64,
        individual_amount: u64,
        bonus_per_member:  u64,
        member_count:      u64,
        _reserved:         u64,
    ) -> Result<()> {

        // ── Guards ────────────────────────────────────────────────
        require!(confidence >= MIN_CONFIDENCE, TheftError::ConfidenceTooLow);
        require!(
            member_count == ctx.remaining_accounts.len() as u64,
            TheftError::MemberCountMismatch
        );

        // ── Snapshot ctx.accounts into owned locals ───────────────
        // By unifying the two lifetime parameters of Context to 'c,
        // the compiler can reconcile remaining_accounts and ctx.accounts
        // accesses in the same scope without invariance conflicts.
        let token_program_key = ctx.accounts.token_program.key();
        let reward_pool_key   = ctx.accounts.reward_pool.key();
        let admin_key         = ctx.accounts.admin.key();
        let reporter_pubkey   = ctx.accounts.reporter_account.key();

        // Read expected_mint from reward_pool raw bytes (SPL offset 0..32)
        let expected_mint = {
            let data = ctx.accounts.reward_pool.try_borrow_data()?;
            Pubkey::try_from(&data[0..32]).map_err(|_| TheftError::MintMismatch)?
        };

        // Verify reporter has same mint
        {
            let data = ctx.accounts.reporter_account.try_borrow_data()?;
            let reporter_mint = Pubkey::try_from(&data[0..32])
                .map_err(|_| TheftError::MintMismatch)?;
            require!(reporter_mint == expected_mint, TheftError::MintMismatch);
        }

        let reward_pool_ai   = ctx.accounts.reward_pool.to_account_info();
        let reporter_ai      = ctx.accounts.reporter_account.to_account_info();
        let admin_ai         = ctx.accounts.admin.to_account_info();
        let token_program_ai = ctx.accounts.token_program.to_account_info();

        // ── 1. Pay the reporter (60%) ─────────────────────────────
        if individual_amount > 0 {
            token::transfer(
                CpiContext::new(
                    token_program_ai.clone(),
                    Transfer {
                        from:      reward_pool_ai.clone(),
                        to:        reporter_ai,
                        authority: admin_ai.clone(),
                    },
                ),
                individual_amount,
            )?;
        }

        // ── 2. Pay each peer (40% / N) via raw invoke ─────────────
        if bonus_per_member > 0 {
            for peer_ai in ctx.remaining_accounts.iter() {
                // Verify mint from raw bytes (SPL TokenAccount: mint = [0..32])
                let data = peer_ai.try_borrow_data()?;
                let peer_mint = Pubkey::try_from(&data[0..32])
                    .map_err(|_| TheftError::MintMismatch)?;
                drop(data);

                require!(peer_mint == expected_mint, TheftError::MintMismatch);

                let ix = spl_instruction::transfer(
                    &token_program_key,
                    &reward_pool_key,
                    peer_ai.key,
                    &admin_key,
                    &[],
                    bonus_per_member,
                )?;

                invoke(
                    &ix,
                    &[
                        reward_pool_ai.clone(),
                        peer_ai.clone(),
                        admin_ai.clone(),
                        token_program_ai.clone(),
                    ],
                )?;
            }
        }

        // ── 3. Update global state ────────────────────────────────
        let state = &mut ctx.accounts.state;

        state.detection_count = state.detection_count
            .checked_add(1)
            .ok_or(TheftError::MathOverflow)?;

        let total_paid = individual_amount
            .checked_add(
                bonus_per_member
                    .checked_mul(member_count)
                    .ok_or(TheftError::MathOverflow)?
            )
            .ok_or(TheftError::MathOverflow)?;

        state.total_rewards = state.total_rewards
            .checked_add(total_paid)
            .ok_or(TheftError::MathOverflow)?;

        // ── 4. Emit on-chain event ────────────────────────────────
        emit!(TheftRewardEvent {
            reporter:          reporter_pubkey,
            community_members: member_count,
            voltage,
            current,
            confidence,
            individual_amount,
            bonus_per_member,
            total_paid,
            timestamp:         Clock::get()?.unix_timestamp,
        });

        msg!(
            "Theft! V={} I={} Conf={}% | {}peers x {} | Total={}",
            voltage, current, confidence,
            member_count, bonus_per_member,
            total_paid,
        );

        Ok(())
    }
}

// ─────────────────────────────────────────────────────────────
//  Account Contexts
// ─────────────────────────────────────────────────────────────

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(
        init,
        payer = admin,
        space = 8 + StateAccount::SIZE,
        seeds = [b"state", admin.key().as_ref()],
        bump
    )]
    pub state: Account<'info, StateAccount>,

    #[account(mut)]
    pub admin: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(community_id: String)]
pub struct CreateCommunity<'info> {
    #[account(
        mut,
        seeds = [b"state", admin.key().as_ref()],
        bump,
        has_one = admin
    )]
    pub state: Account<'info, StateAccount>,

    #[account(
        init,
        payer = admin,
        space = 8 + CommunityAccount::SIZE,
        seeds = [b"community", community_id.as_bytes()],
        bump
    )]
    pub community: Account<'info, CommunityAccount>,

    #[account(mut)]
    pub admin: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(community_id: String, house_id: String)]
pub struct RegisterHouse<'info> {
    #[account(
        mut,
        seeds = [b"community", community_id.as_bytes()],
        bump,
        has_one = admin
    )]
    pub community: Account<'info, CommunityAccount>,

    #[account(
        init,
        payer = admin,
        space = 8 + HouseMember::SIZE,
        seeds = [b"member", community_id.as_bytes(), house_id.as_bytes()],
        bump
    )]
    pub house_member: Account<'info, HouseMember>,

    /// The SPL token account that will receive rewards for this house.
    pub house_token_account: Account<'info, TokenAccount>,

    #[account(mut)]
    pub admin: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct RewardCommunity<'info> {
    #[account(
        mut,
        seeds = [b"state", admin.key().as_ref()],
        bump,
        has_one = admin
    )]
    pub state: Account<'info, StateAccount>,

    #[account(mut)]
    pub admin: Signer<'info>,

    /// SPL token account that funds all rewards.
    /// UncheckedAccount avoids Account<'info,T> invariance conflicts
    /// when also iterating remaining_accounts in the same instruction.
    /// Mint + ownership are verified manually inside reward_community.
    #[account(mut)]
    pub reward_pool: UncheckedAccount<'info>,

    /// Token account of the reporting house.
    #[account(mut)]
    pub reporter_account: UncheckedAccount<'info>,

    pub token_program: Program<'info, Token>,

    // remaining_accounts = peer token accounts (validated inside instruction)
}

// ─────────────────────────────────────────────────────────────
//  On-chain Account Structs
// ─────────────────────────────────────────────────────────────

#[account]
pub struct StateAccount {
    pub admin:            Pubkey,   // 32
    pub total_rewards:    u64,      //  8
    pub detection_count:  u64,      //  8
    pub community_count:  u64,      //  8
}

impl StateAccount {
    pub const SIZE: usize = 32 + 8 + 8 + 8;
}

#[account]
pub struct CommunityAccount {
    pub admin:             Pubkey,   // 32
    pub community_id:      String,   //  4 + 32
    pub member_count:      u64,      //  8
    pub total_rewards:     u64,      //  8
    pub detection_count:   u64,      //  8
}

impl CommunityAccount {
    pub const SIZE: usize = 32 + (4 + 32) + 8 + 8 + 8;
}

#[account]
pub struct HouseMember {
    pub community:       Pubkey,   // 32
    pub house_id:        String,   //  4 + 32
    pub token_account:   Pubkey,   // 32
    pub total_received:  u64,      //  8
    pub detection_count: u64,      //  8
    pub joined_at:       i64,      //  8
}

impl HouseMember {
    pub const SIZE: usize = 32 + (4 + 32) + 32 + 8 + 8 + 8;
}

// ─────────────────────────────────────────────────────────────
//  Events
// ─────────────────────────────────────────────────────────────

#[event]
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

// ─────────────────────────────────────────────────────────────
//  Errors
// ─────────────────────────────────────────────────────────────

#[error_code]
pub enum TheftError {
    #[msg("Only the admin can trigger rewards")]
    Unauthorized,

    #[msg("Math overflow in reward calculation")]
    MathOverflow,

    #[msg("Reward pool and reporter token account mint mismatch")]
    MintMismatch,

    #[msg("member_count must equal the number of remaining_accounts")]
    MemberCountMismatch,

    #[msg("Confidence score below minimum threshold")]
    ConfidenceTooLow,

    #[msg("Community ID must be 32 characters or fewer")]
    CommunityIdTooLong,

    #[msg("House ID must be 32 characters or fewer")]
    HouseIdTooLong,

    #[msg("Community has reached maximum member capacity")]
    CommunityFull,
}
