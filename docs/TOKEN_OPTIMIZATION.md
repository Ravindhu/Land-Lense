# Token optimization

Goal: spend tokens (LLM and OCR) only where they change the result. Applies to coding agents working on this repo and to the daily pipeline that calls Gemini or another model.

## 1. Coding agents (building the repo)

### Keep context small
- Read only the section you need. For `docs/RULES.md`, read section 2 for zone questions; do not load the whole file.
- Use `Grep` or `Glob` to find a symbol or file before opening it.
- Do not paste whole PDFs, GeoJSON files, or OCR dumps into the chat. Refer to them by path and a short summary.
- Start a new session per phase (see `docs/ROADMAP.md`). Carry forward only the decisions from `docs/DECISIONS.md`.
- Keep `AGENTS.md` short. It is read every session; put long detail in the `docs/` files.

### Work in small steps
- One module per change, with its test. Run `make test` on the narrow test file first, then the full suite.
- Ask for a diff or a function, not a full file rewrite, when editing existing code.
- Record a decision once in `docs/DECISIONS.md` instead of repeating it in later prompts.

### Avoid repeated work
- Do not re-read a file already read in the same session unless it changed.
- Do not re-run tests you have not changed code for.

## 2. Daily pipeline (runtime)

The biggest recurring cost is OCR of gazette PDFs. Most gazettes do not change between runs.

### Cache by content hash
- Key every OCR result by the SHA-256 of the PDF, plus the engine and model name. Store the result in `storage/ocr_cache/`.
- If the hash is in the cache, skip the model call. Re-running `daily_sync` should cost almost nothing when nothing new was published.
- Invalidate the cache only when the model or prompt version changes. Store the prompt version with each entry.

### Send only new pages
- Split each PDF by page. Send only pages not yet in the cache.
- Skip pages with no survey-number content (for example a cover page) using a cheap text-layer check before any model call.
- Use the text layer when the PDF has one. Use OCR only for scanned pages.

### Right-size the model
- Run Tesseract (Tamil data) first where its accuracy is good enough on the labelled sample (`docs/TESTING.md` section 3). Send only low-confidence pages to Gemini.
- Use the smallest model that passes the labelled sample. Move up a size only for pages that fail.
- Keep prompts short and fixed. Put the output schema in the prompt once; do not repeat examples.

### Limit output
- Ask for structured JSON only (the Pydantic schema). No prose explanations.
- Ask for survey numbers, stage, and confidence only. Do not ask the model to interpret the law or compute zones; the code does that.

### Use prompt caching where the provider supports it
- The fixed instruction block and schema are the same on every call. Mark them as cacheable if the provider API supports prompt caching.

### Batch
- Batch pages from one gazette into one request where the API allows it. Fewer calls means less overhead.

## 3. Web and source fetching
- Cache fetched pages and collector responses in `storage/http_cache/` with a timestamp. Refetch only when older than the source's refresh interval.
- Respect each source's terms (`docs/SOURCES.md`). Fetching less is also cheaper.
- Store the manifest (hash, date, URL) so a fetch is never repeated for the same file.

## 4. Storage and logs
- Keep GeoJSON files simplified to the precision needed (for example 6 decimal places for coordinates).
- Rotate `audit_log.jsonl` monthly. Keep the archive; do not load the whole log into any prompt.
- Store the OCR result, not the raw model response, unless debugging.

## 5. Budget and monitoring
- Record per run: pages seen, pages cached, pages sent to the model, input and output tokens, and cost estimate.
- Add the figures to the daily status file (`docs/DEPLOYMENT.md` section 5).
- Set a monthly cap in config (`config/settings.yaml`, `llm_budget`). When 80% is reached, send an alert; at 100%, only run cache-hit work and queue the rest for the next month.
- Review the monthly numbers in `docs/DECISIONS.md`.

## 6. What not to optimize
- Accuracy on survey numbers. Never trade it for tokens. Low confidence goes to review, not to a cheaper guess.
- Owner-data checks. These are rules, not model calls. Keep them deterministic.
- Privacy filters. Never skip the redaction step to save a call.

## 7. Checklist before each release
- [ ] Cache hit rate logged for the last 7 days.
- [ ] Pages sent to model below the target in `config/settings.yaml`.
- [ ] Monthly spend within cap.
- [ ] Prompts and schema versioned.
- [ ] No cached result used after a model or prompt change.
