-- ============================================================
-- RAG Pipeline — Supabase Schema
-- Run this in your Supabase SQL editor to create all tables.
-- ============================================================

-- Documents
create table if not exists documents (
    id              uuid primary key default gen_random_uuid(),
    file_name       text not null,
    source_type     text,
    uploaded_at     timestamptz default now(),
    parse_status    text,
    num_chunks      int,
    checksum        text
);

-- Query logs (per-query telemetry)
create table if not exists query_logs (
    id                      uuid primary key default gen_random_uuid(),
    query_text              text not null,
    answer_text             text,
    retrieval_mode          text,
    retrieval_latency_ms    numeric,
    generation_latency_ms   numeric,
    total_latency_ms        numeric,
    input_tokens            int,
    output_tokens           int,
    estimated_cost_usd      numeric,
    llm_model               text,
    embedding_model         text,
    created_at              timestamptz default now()
);

-- Retrieval traces (per-chunk detail per query)
create table if not exists retrieval_logs (
    id                      uuid primary key default gen_random_uuid(),
    query_log_id            uuid references query_logs(id) on delete cascade,
    retriever_type          text,          -- vector | bm25 | hybrid | +reranker
    chunk_id                text,
    file_name               text,
    chunk_index             int,
    retrieval_rank          int,
    retrieval_score         numeric,
    rerank_score            numeric,
    selected_for_generation boolean default false,
    created_at              timestamptz default now()
);

-- Eval run summaries
create table if not exists eval_runs (
    id                      uuid primary key default gen_random_uuid(),
    run_name                text unique not null,
    dataset_version         text,
    config_version          jsonb,
    created_at              timestamptz default now(),
    mean_faithfulness       numeric,
    mean_context_precision  numeric,
    mean_context_recall     numeric,
    mean_answer_relevance   numeric,
    pass_fail               text
);

-- Per-sample eval results
create table if not exists eval_samples (
    id                  uuid primary key default gen_random_uuid(),
    eval_run_id         uuid references eval_runs(id) on delete cascade,
    question            text,
    generated_answer    text,
    faithfulness        numeric,
    context_precision   numeric,
    context_recall      numeric,
    answer_relevance    numeric
);

-- Indexes for common query patterns
create index if not exists idx_query_logs_created_at on query_logs(created_at desc);
create index if not exists idx_retrieval_logs_query_log_id on retrieval_logs(query_log_id);
create index if not exists idx_eval_samples_eval_run_id on eval_samples(eval_run_id);
