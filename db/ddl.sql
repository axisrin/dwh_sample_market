
-- Таблица торговых точек (мерчантов)
CREATE TABLE IF NOT EXISTS public.merchants (
    merchant_id   BIGINT PRIMARY KEY,
    latitude      DOUBLE PRECISION,
    longtitude    DOUBLE PRECISION,
    mcc_cd        INTEGER
);

-- Таблица клиентов
CREATE TABLE IF NOT EXISTS public.clients (
    client_id BIGINT PRIMARY KEY,
    gender    VARCHAR(10),
    age       INTEGER
);

-- Таблица транзакций (факт)
CREATE TABLE IF NOT EXISTS public.transactions (
    transaction_id   BIGSERIAL PRIMARY KEY,
    merchant_id      BIGINT REFERENCES public.merchants(merchant_id),
    client_id        BIGINT REFERENCES public.clients(client_id),
    transaction_dttm TIMESTAMP WITHOUT TIME ZONE,
    transaction_amt  NUMERIC(12,2)
);