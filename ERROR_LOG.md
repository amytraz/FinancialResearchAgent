# 🛠️ ARA-1 Project Error Log
**Intern Name:** Amit Raj Thakur  
**Project:** Autonomous Financial Research Agent (ARA-1)

---

## 🔍 Part 1: Simulation "Bug Hunt" (Document Errors)
*These are the 7 deliberate factual or logical errors found within the ZeTheta project documentation.*

| # | Location | Detected Error | Correction / Reality |
| :--- | :--- | :--- | :--- |
| 1 | Page 19, AB-4 | Metric is calculated as `memory_hits` multiplied by `total_api_calls`. | A "utilization" metric must be a ratio. [cite_start]Correct formula: `memory_hits / total_api_calls`. [cite: 383, 384] |
| 2 | Page 24, A7.3 | Claims first US bank stress tests (SCAP) were in 2007 via Dodd-Frank. | [cite_start]The Dodd-Frank Act was passed in 2010; the first SCAP tests were actually in 2009. [cite: 481] |
| 3 | Page 21, A6.2 | Ranks Tier 4 as "Social Media" and Tier 5 as "Major News Outlets". | [cite_start]Professional hierarchy should prioritize Tier 5 (News Outlets like Bloomberg/Reuters) over Tier 4 (Social Media). [cite: 413, 414] |
| 4 | Page 10, A2.4 | JSON Schema code block has invalid syntax for the `ticker` property. | [cite_start]The curly braces for the property object are misplaced in the example. [cite: 176, 181] |
| 5 | Page 7, A2.2 | Input schema for `sec_filing_search` lists `ticker: str, NO`. | [cite_start]`NO` is not a valid schema type; it is likely a typo for `required` or `None`. [cite: 141] |
| 6 | Page 42, C4.2 | Claims Indian companies file annual returns using Form 20-F. | Indian companies use Form MGT-7 or AOC-4. [cite_start]Form 20-F is a US SEC form for foreign issuers. [cite: 827] |
| 7 | Page 18, FA-5 | Target Hallucination rate is 0 on page 18, but "below 2%" on page 2. | Inconsistency in evaluation metrics. [cite_start]Professional standard target is <2%, ideal is 0. [cite: 28, 342] |

---

## 💻 Part 2: Technical Execution Log
*This section tracks bugs encountered during the local build of the Python agent.*

| Date | Category | Description | Resolution |
| :--- | :--- | :--- | :--- |
| 2026-04-12 | Environment | `.env` variables not loading in `core.py`. | Installed `python-dotenv` and added `load_dotenv()` call. |
| 2026-04-12 | Tool Registry | JSON Schema validation error for `sec_edgar.json`. | Corrected nesting of "properties" block in JSON file. |
| 2026-04-12 | API | SEC EDGAR blocked request with 403 Forbidden. | Added mandatory `User-Agent` header with name and email to request. |
| 2026-04-12 | Import | `ModuleNotFoundError: tools.sec_edgar` — Python code was saved in the `.json` schema file. | Created `tools/sec_edgar.py` correctly; restored `sec_edgar.json` as valid JSON. |
| 2026-04-12 | Missing Module | `langchain_chroma`, `langchain_text_splitters`, `langchain_groq` not installed. | Added all three to `requirements.txt` and installed into venv. |
| 2026-04-12 | LLM | OpenAI quota exceeded (429). | Replaced `ChatOpenAI` with `ChatGroq` (free tier). |
| 2026-04-12 | LLM | Groq model `llama3-70b-8192` decommissioned (404). | Updated fallback model to `llama-3.3-70b-versatile`. |
| 2026-04-12 | Embeddings | `OpenAIEmbeddings` in `vector_store.py` required `OPENAI_API_KEY`. | Replaced with `HuggingFaceEmbeddings(all-MiniLM-L6-v2)` — runs locally, zero cost. |
| 2026-04-12 | Tool Failure | `tool_use_failed` 400 — Groq LLaMA generating malformed XML when calling tools in parallel. | Redesigned to deterministic OODA pipeline; LLM no longer generates tool calls. Tools are invoked as Python functions. |
| 2026-04-12 | Data Quality | `sec_filing_search` returned `MOCK OUTPUT`, causing agent to loop indefinitely. | Replaced with real SEC EDGAR API calls (`data.sec.gov/submissions`). |
| 2026-04-13 | Schema Drift | `'int' object has no attribute 'date'` in `get_analyst_ratings` — yfinance recommendations index type changed. | Added defensive date parser with `hasattr` checks; validates DataFrame type before iterating. |
| 2026-04-13 | Throughput | Groq 429 rate-limit during synthesis — unbounded context window from full tool outputs in `AgentState`. | Implemented **Summary Buffer** pattern: tool results capped at 700 chars in state; full text persists in ChromaDB. |
| 2026-04-13 | Latency | Serial tool execution (4 tools × ~2s each = 8s). | Implemented **Fan-out** via `ThreadPoolExecutor` — all 4 tools run concurrently. |
| 2026-04-13 | Reliability | No retry logic on synthesis LLM call — single 429 causes full crash. | Wrapped with `tenacity` exponential back-off (2^x seconds, max 4 retries). |

---

## 📊 Part 3: Industrial Error Classification

| Error Code | Industrial Class | Root Cause | Architectural Resolution |
| :--- | :--- | :--- | :--- |
| 429 | **Throughput Saturation** | Unbounded context window — full tool outputs stored in `AgentState` inflated the synthesis prompt beyond Groq's token/rate limit. | Implemented **Summary Buffer** (700 char cap per result in state). Full text stored in ChromaDB. |
| 404 | **Provider Drift** | `yfinance` internal schema change — `recommendations` DataFrame index changed from `Timestamp` to `int`. | Added **Pydantic-style defensive validator** with `hasattr(idx, 'date')` guard and string fallback. |
| Looping | **State Oscillation** | LLM lacked "termination logic" — kept re-calling `sec_filing_search` because it didn't track prior tool results. | Replaced reactive loop with **deterministic OODA pipeline** — researcher node is a fixed-sequence Python executor, not LLM-driven. |
| tool_use_failed | **Model Incompatibility** | Groq's LLaMA 3.3 generates malformed XML when asked to call multiple tools in a single response. | Removed LLM tool-calling entirely. Tools invoked as Python callables via `ThreadPoolExecutor`. |

---

## 📈 Summary of Fixes
* **Total Document Errors Found:** 7/7
* **Total Code Bugs Resolved:** 14
* **Architecture Version:** v3.0 — Deterministic OODA Pipeline with Parallel Fan-out + Tenacity Backoff