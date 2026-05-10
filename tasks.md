# Production RAG Pipeline — Execution Tasks

This document converts the PRD into an implementation sequence that can be executed phase by phase. Each phase includes objectives, tasks, deliverables, exit criteria, and practical notes so development stays structured and reproducible.

---

# 1. Working Rules

## Core Rules

1. Build only one phase at a time.
2. Do not start advanced retrieval features before baseline vector RAG works end to end.
3. After each phase, verify the system manually before moving forward.
4. Keep code modular by responsibility.
5. Prefer correctness and inspectability over premature abstraction.
6. Every feature should be testable in isolation.
7. Maintain a clear config layer for all tunable values.
8. Log enough metadata to debug retrieval quality later.
9. Do not claim evaluation improvements until benchmark data proves them.
10. Preserve the ability to compare retrieval behavior before and after each improvement.

## Definition of Done for Any Phase

A phase is done only when:

* code is implemented
* local run path is documented
* manual verification is completed
* obvious failure cases are handled
* output is inspectable for debugging

---

# 2. Recommended Execution Order

1. Project setup
2. Baseline upload + ingestion + vector RAG
3. BM25 lexical retrieval
4. Hybrid fusion with RRF
5. Cross-encoder reranking
6. Evaluation dataset and RAGAS benchmark
7. Tuning loop
8. Observability and Supabase logging
9. CI-gated benchmark
10. UX polish and debug tooling

---

# 3. Phase 0 — Project Setup

## Objective

Create the initial codebase structure, environment management, local development flow, and shared configuration.

## Tasks

### 0.1 Initialize repository structure

* Create `apps/web` for the Next.js frontend.
* Create `apps/api` for the Python backend.
* Create `data/` directory for raw, processed, and eval assets.
* Create `infra/` for SQL and CI files.
* Create `docs/` for architecture, PRD, and decisions.

### 0.2 Initialize frontend

* Scaffold Next.js app with TypeScript.
* Add minimal layout for upload and chat screens.
* Add shared UI components folder.
* Add environment variable support.

### 0.3 Initialize backend

* Scaffold Python app structure.
* Choose framework for API layer, preferably FastAPI.
* Add app entrypoint.
* Add settings/config module.
* Add route folders and service folders.

### 0.4 Dependency setup

Frontend dependencies:

* Next.js
* React
* TypeScript
* basic UI library only if needed

Backend dependencies:

* FastAPI
* Uvicorn
* LangChain
* ChromaDB
* rank-bm25
* transformers or sentence-transformers for reranker later
* RAGAS later, but dependency can be deferred until Phase 5
* Supabase client
* pydantic and config helpers

### 0.5 Environment and secrets management

* Create `.env.example` for both frontend and backend.
* Define placeholders for:

  * LLM API key
  * embedding model config
  * Supabase URL
  * Supabase key
  * Chroma persistence path
* Document env loading.

### 0.6 Developer scripts

* Add backend run command.
* Add frontend run command.
* Add lint/format commands.
* Add a simple README setup section.

## Deliverables

* Working repo structure
* frontend starts locally
* backend starts locally
* env files documented

## Exit Criteria

* `web` starts without crashing
* `api` starts without crashing
* local developer can understand how to boot both services

---

# 4. Phase 1 — Baseline Vector RAG

## Objective

Build a minimal but complete upload-to-answer pipeline using only chunking, embeddings, vector retrieval, and answer generation.

## Tasks

### 1.1 File upload flow

Frontend:

* Add file upload UI
* Add upload progress or status messaging
* Display success or failure state

Backend:

* Add upload endpoint
* Save uploaded files to a controlled location or process directly
* Validate file types

### 1.2 Document parsing

* Implement parser(s) for initial supported file types, ideally PDF and TXT first
* Extract raw text cleanly
* Handle parser failures gracefully
* Return parse status and metadata

### 1.3 Text cleaning and normalization

* Remove repeated whitespace
* Normalize line breaks
* Preserve section boundaries where possible
* Keep parsing logic inspectable and not overcomplicated initially

### 1.4 Chunking

* Implement configurable text splitting
* Store chunk text and metadata
* Include fields such as:

  * document ID
  * chunk index
  * file name
  * page number if available
  * section title if available
* Make chunk size and overlap configurable

### 1.5 Embedding generation

* Select embedding model
* Generate embeddings for all chunks
* Store embedding metadata consistently

### 1.6 ChromaDB indexing

* Create vector store wrapper
* Insert chunks with metadata and embeddings
* Persist index locally
* Add lookup by document/chunk IDs where feasible

### 1.7 Query endpoint

* Add `/query` endpoint
* Accept natural language question
* Generate query embedding
* Retrieve top-k vector matches
* Return retrieved chunks for debugging

### 1.8 Prompt construction

* Build simple grounded prompt template
* Include only retrieved chunks and user query
* Instruct model to answer only from context
* Ask it to say when context is insufficient

### 1.9 Answer generation

* Call LLM using retrieved chunks
* Return answer plus basic source references

### 1.10 Frontend chat flow

* Add question input
* Display answer
* Display retrieved source chunks or source references below answer

## Deliverables

* upload documents
* index chunks in ChromaDB
* ask question
* get answer based on retrieved vector chunks

## Exit Criteria

* end-to-end upload to answer works locally
* answers show source evidence
* developer can inspect retrieved chunks per query

## Manual Verification Checklist

* upload 1 document and ask a direct factual question
* upload multiple documents and ask which one contains a fact
* ask a question not answered by context and verify the answer does not confidently fabricate
* inspect whether retrieved chunks are sensible

---

# 5. Phase 2 — BM25 Lexical Retrieval

## Objective

Add keyword-based retrieval to complement vector search.

## Tasks

### 2.1 BM25 corpus builder

* Build corpus from stored chunk text
* Maintain mapping between BM25 corpus index and chunk IDs
* Ensure text normalization for lexical search remains simple and reproducible

### 2.2 BM25 retriever service

* Create dedicated retriever module
* Accept query string
* Return top-k chunk candidates with BM25 score and chunk metadata

### 2.3 Retrieval debugging output

* Expose BM25 result list separately from vector result list
* Allow side-by-side comparison during development

### 2.4 Backend integration

* Extend query pipeline to optionally run BM25 retrieval in addition to vector retrieval
* Add feature flag or config toggle for retrieval mode:

  * vector only
  * BM25 only
  * hybrid later

## Deliverables

* BM25 retrieval service
* debug output for lexical retrieval candidates

## Exit Criteria

* keyword-heavy queries return sensible BM25 matches
* exact phrase or identifier queries perform better than vector-only in relevant cases

## Manual Verification Checklist

* ask a query with exact section number or identifier
* ask a query with rare keyword
* compare BM25 vs vector results for same query

---

# 6. Phase 3 — Hybrid Retrieval with RRF

## Objective

Combine lexical and semantic retrieval into a unified ranking.

## Tasks

### 3.1 RRF utility

* Create an RRF function that accepts ranked result lists
* Support configurable fusion constant
* Merge duplicate chunk hits by chunk ID

### 3.2 Candidate normalization

* Normalize candidate structures from BM25 and vector retrievers into a shared schema
* Store source retriever type, original rank, and raw score

### 3.3 Hybrid retrieval orchestrator

* Run vector retrieval
* Run BM25 retrieval
* Fuse rankings using RRF
* Return final ordered candidate set

### 3.4 Debug trace support

* For each final candidate, preserve:

  * whether it came from vector retrieval
  * whether it came from BM25 retrieval
  * original ranks in each retriever
  * fused RRF score

### 3.5 Query mode integration

* Add config option so generation can use fused candidates rather than vector-only candidates

## Deliverables

* hybrid retrieval implementation
* traceable fusion output

## Exit Criteria

* hybrid retrieval works for both semantic and keyword-heavy questions
* fused ranking is inspectable and explainable

## Manual Verification Checklist

* compare vector-only vs hybrid on paraphrased query
* compare vector-only vs hybrid on exact keyword query
* verify chunks found by both retrievers rise in rank appropriately

---

# 7. Phase 4 — Cross-Encoder Reranking

## Objective

Improve final context precision by reranking fused candidates using a cross-encoder.

## Tasks

### 4.1 Reranker model integration

* Add model loading for `BAAI/bge-reranker-base` or equivalent
* Create a reranker service interface

### 4.2 Candidate scoring

* Accept query and top-N fused candidates
* Score each query-chunk pair with reranker
* Return reranked results in descending relevance order

### 4.3 Final context selection

* Choose top-M reranked chunks for final prompt context
* Keep N and M configurable

### 4.4 Query pipeline integration

* Add reranking step after fusion and before generation
* Preserve both pre-rerank and post-rerank ranking for traceability

### 4.5 Performance safeguards

* Do not rerank too many candidates initially
* Make rerank depth configurable
* Track reranking latency for later telemetry

## Deliverables

* reranker service
* reranked final evidence selection

## Exit Criteria

* final generation uses reranked evidence
* manual inspection shows less noisy context than fused retrieval alone

## Manual Verification Checklist

* inspect a query where hybrid retrieval includes partially relevant chunks
* verify reranker promotes the best chunk(s)
* verify reranker does not obviously break exact-match queries

---

# 8. Phase 5 — Evaluation Dataset and RAGAS

## Objective

Create a reproducible benchmark and score the system quantitatively.

## Tasks

### 5.1 Eval dataset design

* Create an initial benchmark with 30 to 100 strong questions
* Include reference answers
* Include expected support context or document references where feasible
* Store dataset versioned in `data/eval/`

### 5.2 Benchmark coverage

Ensure the benchmark includes:

* direct fact lookup questions
* keyword-heavy exact-match questions
* paraphrased semantic questions
* multi-sentence context questions
* insufficient-context questions if supported product behavior matters

### 5.3 Eval runner script

* Implement script to run benchmark questions through pipeline
* Save generated answers and retrieved contexts
* Persist outputs in structured format

### 5.4 RAGAS integration

* Compute metrics:

  * Faithfulness
  * Context Precision
  * Context Recall
  * Answer Relevance
* Produce both aggregate and per-sample results

### 5.5 Eval result storage

* Save benchmark summary locally first
* Later mirror aggregate results to Supabase in Phase 7

### 5.6 Baseline recording

* Run benchmark on baseline vector-only system if still available
* Run benchmark on hybrid system
* Run benchmark on hybrid plus reranking system
* Record comparative metrics honestly

## Deliverables

* versioned eval dataset
* benchmark runner
* RAGAS metric output
* comparison notes across pipeline versions

## Exit Criteria

* metrics are reproducible
* benchmark can be rerun on demand
* at least one meaningful system comparison is recorded

## Manual Verification Checklist

* inspect low-scoring examples
* verify metric outputs correspond to real failure modes
* confirm benchmark questions are not trivial or duplicated

---

# 9. Phase 6 — Tuning and Retrieval Improvement Loop

## Objective

Use measured results to improve retrieval quality systematically.

## Tasks

### 6.1 Define tunable parameters

Create a config matrix for experiments across:

* chunk size
* chunk overlap
* vector top-k
* BM25 top-k
* fusion constant for RRF
* rerank candidate depth
* final context chunk count
* prompt style

### 6.2 Run controlled experiments

* change one or two variables at a time
* rerun benchmark
* record metrics and notes
* identify tradeoffs between recall, precision, latency, and cost

### 6.3 Failure analysis

For poor-performing benchmark cases, inspect:

* chunking issues
* retrieval miss
* fusion ranking issue
* reranker misordering
* prompt/generation failure

### 6.4 Improvement tracking

* maintain simple experiment log in markdown or structured JSON
* capture what changed and why metrics moved

## Deliverables

* experiment notes
* tuned config values
* benchmark evidence of improvement

## Exit Criteria

* retrieval quality is materially improved over baseline
* metric movement is understood, not accidental

---

# 10. Phase 7 — Observability and Supabase Logging

## Objective

Log runtime behavior so cost, latency, and retrieval quality can be monitored.

## Tasks

### 7.1 Supabase schema

Create tables for:

* documents
* chunks metadata if needed
* query_logs
* retrieval_logs
* eval_runs
* eval_samples

### 7.2 Query telemetry logging

For each query, log:

* query text
* timestamps
* retrieval latency
* rerank latency
* generation latency
* total latency
* input tokens
* output tokens
* estimated cost
* model names

### 7.3 Retrieval trace logging

Log per retrieved candidate:

* retriever type
* chunk ID
* original rank
* raw score
* fused score if applicable
* rerank score if applicable
* selected_for_generation flag

### 7.4 Cost estimation

* compute approximate per-query cost from token usage and model pricing assumptions
* isolate pricing logic in one helper module

### 7.5 Dashboard support

At minimum, enable simple querying for:

* p50 latency
* p95 latency
* average cost per query
* most retrieved chunks/documents
* most common failure patterns

## Deliverables

* working Supabase schema
* logged query-level telemetry
* retrieval traces persisted

## Exit Criteria

* every query produces a stored trace
* latency and cost can be inspected after system use

---

# 11. Phase 8 — CI-Gated Evaluation

## Objective

Block merges when benchmark quality drops below threshold.

## Tasks

### 8.1 GitHub Action workflow

* create workflow file
* set up Python environment
* install dependencies
* run benchmark script

### 8.2 Threshold enforcement

* define minimum acceptable metric thresholds
* compare current results with thresholds
* fail CI if below threshold

### 8.3 Artifact and summary output

* print metric summary in CI logs
* optionally upload benchmark artifact

### 8.4 Baseline versioning

* keep benchmark dataset and config versioned so CI results remain interpretable

## Deliverables

* CI workflow for benchmark run
* automatic pass/fail behavior based on metrics

## Exit Criteria

* PRs fail when metrics drop below thresholds
* benchmark results are visible in CI logs

---

# 12. Phase 9 — UX, Inspection, and Demo Polish

## Objective

Make the project easier to demo, inspect, and discuss in interviews.

## Tasks

### 9.1 Retrieval inspector UI

* show vector results
* show BM25 results
* show fused ranking
* show reranked final selection

### 9.2 Source-aware answer panel

* display supporting chunks clearly
* allow user to inspect source document and metadata

### 9.3 Debug metadata

* display latency, token usage, and cost for current query
* optionally show which retrieval mode was used

### 9.4 Error handling

* graceful upload error messages
* graceful parse failure messages
* graceful retrieval/generation failure states

### 9.5 Demo readiness

* prepare seed documents
* prepare 5 to 10 benchmark demo questions
* ensure app runs cleanly for screen recording or live demo

## Deliverables

* inspection-friendly interface
* demo-ready project behavior

## Exit Criteria

* non-author can understand the system behavior from UI
* retrieval pipeline is explainable live during demo

---

# 13. Suggested Backend Task Breakdown by Module

## ingestion/

Tasks:

* file validators
* parsers
* text cleaners
* chunkers
* metadata extractors
* embedding writers
* vector indexer integration

## retrieval/

Tasks:

* vector retriever
* BM25 retriever
* RRF fuser
* candidate schema normalizer
* retrieval orchestrator

## reranking/

Tasks:

* model loader
* query-document scoring
* rerank service wrapper

## generation/

Tasks:

* prompt templates
* context formatter
* answer generator
* citation formatter

## evaluation/

Tasks:

* dataset loader
* benchmark runner
* RAGAS integration
* experiment result serializer

## telemetry/

Tasks:

* latency timers
* token usage collector
* cost estimator
* Supabase logging writer

---

# 14. Suggested Frontend Task Breakdown

## Upload Experience

* upload form
* file status list
* success/failure feedback

## Chat Experience

* query input
* answer rendering
* source rendering
* loading state

## Inspector Panels

* retrieval trace view
* metrics view
* debug metadata view

---

# 15. Testing Tasks

## Unit Tests

* chunking outputs
* RRF scoring behavior
* BM25 retriever behavior
* reranker integration wrapper
* cost estimation helper

## Integration Tests

* upload to indexing flow
* vector retrieval query flow
* hybrid retrieval query flow
* reranked answer generation flow

## Benchmark Validation

* benchmark file schema validation
* metric output validation

---

# 16. Documentation Tasks

## Must-Have Docs

* setup instructions
* architecture overview
* retrieval pipeline explanation
* evaluation methodology
* benchmark design notes
* tuning log

## Nice-to-Have Docs

* interview talking points
* common failure cases
* future scaling paths

---

# 17. Suggested Milestone Checkpoints

## Milestone A

Baseline vector RAG works end to end.

## Milestone B

BM25 plus hybrid retrieval works and is inspectable.

## Milestone C

Cross-encoder reranking improves final evidence quality.

## Milestone D

Benchmark dataset and RAGAS scoring are reproducible.

## Milestone E

System logs latency, token usage, and cost.

## Milestone F

CI blocks quality regressions automatically.

## Milestone G

Project is portfolio-ready and demo-ready.

---

# 18. Anti-Patterns to Avoid

1. Do not build UI polish before baseline retrieval works.
2. Do not add reranking before proving hybrid retrieval works.
3. Do not trust “looks better” without benchmark evidence.
4. Do not hide retrieval traces; inspectability is essential.
5. Do not hardcode magic numbers without config.
6. Do not overload the prompt with too many chunks.
7. Do not claim production-grade quality without observability and regression protection.
8. Do not merge changes that alter retrieval without rerunning evaluation.

---

# 19. Final Goal

By the end of execution, the project should demonstrate:

* a complete production-style RAG architecture
* measurable retrieval and answer quality
* eval-driven tuning discipline
* regression protection in CI
* operational telemetry for latency and cost
* a polished enough interface to explain the system clearly in interviews and demos

---

# 20. Immediate Next Action for Claude Code

Start with only these tasks now:

* Phase 0 repository and environment setup
* Phase 1 baseline upload, chunking, Chroma indexing, vector retrieval, prompt construction, answer generation, and minimal chat UI

Do not start BM25, RRF, reranking, or RAGAS until baseline vector RAG is fully working and manually verified.


your code will be reviewed by codex.