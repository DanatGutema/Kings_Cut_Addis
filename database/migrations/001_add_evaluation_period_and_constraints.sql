-- Run against an existing KingsCutAddis database created from the original schema.

ALTER TABLE loyalty_rules
    ADD COLUMN IF NOT EXISTS evaluation_period_days INTEGER;

COMMENT ON COLUMN loyalty_rules.evaluation_period_days IS
    'Rolling window in days for visit/spend thresholds. NULL means all-time.';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_promotion_recipient'
    ) THEN
        ALTER TABLE promotion_recipients
            ADD CONSTRAINT uq_promotion_recipient
            UNIQUE (promotion_id, customer_id);
    END IF;
END $$;
