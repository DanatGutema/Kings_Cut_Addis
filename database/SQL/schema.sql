
--core business database table (customers, staff, services, visits, loyalty, rewards,
-- and promotions).

CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT UNIQUE,   --need to decide to make nulable or not
    -- for the customer who are using phone number to register, telegram_id will be null
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255),
    phone_number VARCHAR(15) NOT NULL UNIQUE,
    email VARCHAR(255) UNIQUE,    --THIS IS OPTIONAL FIELD THAT I ADDED
    qr_token UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    total_visits INTEGER NOT NULL DEFAULT 0,
    total_spending DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    joined_date DATE NOT NULL DEFAULT CURRENT_DATE,
    last_visit_date DATE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);



CREATE TABLE staff (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255),
    phone_number VARCHAR(15) NOT NULL UNIQUE,
    email VARCHAR(255)  NOT NULL UNIQUE,   
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'staff',
                     CHECK (role IN ('admin', 'staff')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login TIMESTAMP
);


CREATE TABLE services (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL UNIQUE,
    price       DECIMAL(10, 2) NOT NULL,
    description TEXT,
    duration_minutes  INTEGER,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP NOT NULL DEFAULT NOW()
);



CREATE TABLE visits (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    customer_id UUID NOT NULL,

    staff_id UUID NOT NULL,

    visit_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    total_amount DECIMAL(12,2) NOT NULL,

    notes TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_visit_customer
        FOREIGN KEY(customer_id)
        REFERENCES customers(id),

    CONSTRAINT fk_visit_staff
        FOREIGN KEY(staff_id)
        REFERENCES staff(id)

);



CREATE TABLE visit_services (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    visit_id UUID NOT NULL,

    service_id UUID NOT NULL,

    quantity INTEGER NOT NULL DEFAULT 1,

    unit_price DECIMAL(12,2) NOT NULL,

    subtotal DECIMAL(12,2) NOT NULL,

    CONSTRAINT fk_vs_visit
        FOREIGN KEY(visit_id)
        REFERENCES visits(id),

    CONSTRAINT fk_vs_service
        FOREIGN KEY(service_id)
        REFERENCES services(id)

);



CREATE TABLE loyalty_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    rule_name VARCHAR(255) NOT NULL,

    rule_type VARCHAR(30) NOT NULL
        CHECK (
            rule_type IN ('visit','spending')
        ),

    visit_threshold INTEGER,

    spending_threshold DECIMAL(12,2),

    reward_type VARCHAR(30) NOT NULL
        CHECK (
            reward_type IN
            ('percentage','fixed','both')
        ),

    reward_percentage DECIMAL(5,2),

    reward_amount DECIMAL(12,2),

  expiry_days INTEGER NOT NULL,

    -- Rolling window for visit/spend thresholds (NULL = all-time)
    evaluation_period_days INTEGER,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);



CREATE TABLE rewards (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    customer_id UUID NOT NULL,

    loyalty_rule_id UUID NOT NULL,

    reward_type VARCHAR(30) NOT NULL,

    reward_percentage DECIMAL(5,2),

    reward_amount DECIMAL(12,2),

    earned_date DATE NOT NULL,

    expiry_date DATE NOT NULL,

    status VARCHAR(30)
        DEFAULT 'pending'
        CHECK (
            status IN
            ('pending','redeemed','expired','void')
        ),

    redeemed_at TIMESTAMP,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_reward_customer
        FOREIGN KEY(customer_id)
        REFERENCES customers(id),

    CONSTRAINT fk_reward_rule
        FOREIGN KEY(loyalty_rule_id)
        REFERENCES loyalty_rules(id)

);



CREATE TABLE reward_history (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    reward_id UUID NOT NULL,

    action VARCHAR(30)
        CHECK (
            action IN
            ('earned','redeemed','expired','void')
        ),

    action_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    staff_id UUID,

    remarks TEXT,

    CONSTRAINT fk_history_reward
        FOREIGN KEY(reward_id)
        REFERENCES rewards(id),

    CONSTRAINT fk_history_staff
        FOREIGN KEY(staff_id)
        REFERENCES staff(id)

);


CREATE TABLE promotions (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    title VARCHAR(255) NOT NULL,

    description TEXT,

    discount_type VARCHAR(30)
        CHECK (
            discount_type IN
            ('percentage','fixed')
        ),

    discount_value DECIMAL(12,2),

    start_date DATE NOT NULL,

    end_date DATE NOT NULL,

    is_active BOOLEAN DEFAULT TRUE,

    media_type VARCHAR(20)
        CHECK (media_type IS NULL OR media_type IN ('photo','video')),

    media_filename VARCHAR(255),

    created_by UUID NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_promotion_staff
        FOREIGN KEY(created_by)
        REFERENCES staff(id)

);



CREATE TABLE promotion_recipients (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    promotion_id UUID NOT NULL,

    customer_id UUID NOT NULL,

    telegram_sent BOOLEAN DEFAULT FALSE,

    sms_sent BOOLEAN DEFAULT FALSE,

    delivered BOOLEAN DEFAULT FALSE,

    delivered_at TIMESTAMP,

    CONSTRAINT fk_pr_promotion
        FOREIGN KEY(promotion_id)
        REFERENCES promotions(id),

    CONSTRAINT fk_pr_customer
        FOREIGN KEY(customer_id)
        REFERENCES customers(id),

    CONSTRAINT uq_promotion_recipient
        UNIQUE (promotion_id, customer_id)

);




--Infrastructure Layer of the database

CREATE TABLE refresh_tokens (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    customer_id UUID,

    staff_id UUID,

    token_hash TEXT NOT NULL,

    device_name VARCHAR(255),

    device_type VARCHAR(50),

    ip_address VARCHAR(50),

    expires_at TIMESTAMP NOT NULL,

    revoked BOOLEAN NOT NULL DEFAULT FALSE,

    revoked_at TIMESTAMP,

    last_used_at TIMESTAMP,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_refresh_customer
        FOREIGN KEY(customer_id)
        REFERENCES customers(id),

    CONSTRAINT fk_refresh_staff
        FOREIGN KEY(staff_id)
        REFERENCES staff(id),

    CHECK (
        (customer_id IS NOT NULL AND staff_id IS NULL)
        OR
        (customer_id IS NULL AND staff_id IS NOT NULL)
    )
);




CREATE TABLE customer_sessions (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    customer_id UUID NOT NULL,

    login_method VARCHAR(30)
        CHECK (
            login_method IN
            ('telegram','otp')
        ),

    device_name VARCHAR(255),

    ip_address VARCHAR(50),

    login_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    logout_time TIMESTAMP,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT fk_session_customer
        FOREIGN KEY(customer_id)
        REFERENCES customers(id)

);



CREATE TABLE sms_logs (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    customer_id UUID NOT NULL,

    phone_number VARCHAR(20) NOT NULL,

    message TEXT NOT NULL,

    sms_type VARCHAR(30)
        CHECK (
            sms_type IN
            ('promotion','otp','notification')
        ),

    provider VARCHAR(100),

    delivery_status VARCHAR(30)
        DEFAULT 'pending'
        CHECK (
            delivery_status IN
            ('pending','sent','delivered','failed')
        ),

    provider_reference VARCHAR(255),

    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    delivered_at TIMESTAMP,

    CONSTRAINT fk_sms_customer
        FOREIGN KEY(customer_id)
        REFERENCES customers(id)

);



CREATE TABLE telegram_logs (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    customer_id UUID NOT NULL,

    telegram_id BIGINT NOT NULL,

    message TEXT NOT NULL,

    message_type VARCHAR(30)
        CHECK (
            message_type IN
            ('promotion','notification','reward')
        ),

    telegram_message_id BIGINT,

    delivery_status VARCHAR(30)
        DEFAULT 'sent'
        CHECK (
            delivery_status IN
            ('sent','failed')
        ),

    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_telegram_customer
        FOREIGN KEY(customer_id)
        REFERENCES customers(id)

);



CREATE TABLE system_settings (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    setting_key VARCHAR(255) NOT NULL UNIQUE,

    setting_value TEXT NOT NULL,

    description TEXT,

    updated_by UUID,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_setting_staff
        FOREIGN KEY(updated_by)
        REFERENCES staff(id)

);


CREATE TABLE audit_logs (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    staff_id UUID,

    action VARCHAR(100) NOT NULL,

    table_name VARCHAR(100),

    record_id UUID,

    old_data JSONB,

    new_data JSONB,

    ip_address VARCHAR(50),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_audit_staff
        FOREIGN KEY(staff_id)
        REFERENCES staff(id)

);


CREATE TABLE service_orders(

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    customer_id UUID NOT NULL,

    status VARCHAR(30)
        DEFAULT 'pending'
        CHECK (
            status IN
            ('pending','confirmed','in_progress','completed','cancelled')
        ),

    scheduled_at TIMESTAMP NOT NULL,
    prefered_time_slot VARCHAR(50) NOT NULL,

    total_estimated_price DECIMAL(10, 2) NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_service_order_customer
        FOREIGN KEY(customer_id)
        REFERENCES customers(id)

);

CREATE TABLE service_order_items(

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    service_order_id UUID NOT NULL,

    service_id UUID NOT NULL,

    quantity INTEGER NOT NULL DEFAULT 1,

    unit_price DECIMAL(10, 2) NOT NULL,

    subtotal DECIMAL(10, 2) NOT NULL,

    CONSTRAINT fk_soi_service_order
        FOREIGN KEY(service_order_id)
        REFERENCES service_orders(id),

    CONSTRAINT fk_soi_service
        FOREIGN KEY(service_id)
        REFERENCES services(id)

);














---------------------------------------------------
-- INDEXES
---------------------------------------------------

CREATE INDEX idx_customer_phone
ON customers(phone_number);

CREATE INDEX idx_customer_telegram
ON customers(telegram_id);

CREATE INDEX idx_visit_customer
ON visits(customer_id);

CREATE INDEX idx_visit_date
ON visits(visit_date);

CREATE INDEX idx_reward_customer
ON rewards(customer_id);

CREATE INDEX idx_reward_status
ON rewards(status);

CREATE INDEX idx_sms_status
ON sms_logs(delivery_status);

CREATE INDEX idx_telegram_status
ON telegram_logs(delivery_status);

CREATE INDEX idx_refresh_token
ON refresh_tokens(token_hash);

CREATE INDEX idx_order_customer
ON service_orders(customer_id);

CREATE INDEX idx_order_status
ON service_orders(status);

CREATE INDEX idx_service_order_items_order
ON service_order_items(service_order_id);

CREATE INDEX idx_service_order_items_service
ON service_order_items(service_id);