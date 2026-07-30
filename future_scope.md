# RetailForecastAI — Future Scope

Ideas for extending the project beyond its current state. Grouped by effort/impact.

## Near-term (fills real gaps)

- **Push the pending local commits.** 8+ logically-grouped commits sit locally ahead of `origin/main` as of 2026-07-13 (Next.js frontend, RAG generation endpoint, dashboard rework). Not pushed — user pushes manually. Verify CI passes once pushed.
- **Click-to-zoom / expand chart modal.** Requested for the dashboard Overview tab: clicking a chart enlarges it over a dimmed backdrop, other content hides behind it. Explicitly deferred until after the Overview space-efficiency rework (now done) — this is the next dashboard UI task.
- **Fix the broken `.venv/bin/uvicorn` shebang.** Its shebang line points at a stale path from before the project directory was renamed (`RetailForecastAI` → `retail-forecast-ai`), so `make run` / direct `.venv/bin/uvicorn ...` fails with "No such file or directory". Current workaround: `.venv/bin/python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8080`. Proper fix: recreate the venv (`make install`) so the shebang is regenerated with the correct path, or update the Makefile to always invoke via `python -m uvicorn`.
- **Wire up Tableau.** Mentioned in the README tech stack as *(in progress)* — user has a workbook they plan to integrate for deeper fleet-level BI analytics alongside the Next.js dashboard and Streamlit tool. Not yet in the repo.
- **Delete `scripts/commit_groups.sh`.** A one-off commit-grouping helper from this session, superseded by making real commits directly. Sitting untracked in the repo; user said they'd delete it themselves — don't recreate it.
- **Continue the local narrative batch.** 20/1,115 stores had saved narratives as of the last count (`STORE_0001`–`STORE_0020`), though the new live "Generate AI analysis" button (dashboard Store Forecast / AI Narrative tabs, `POST /v1/narrative/{id}/generate`) now lets any store's narrative be generated and persisted on demand, one at a time, from the UI itself — the CLI batch script is still useful for bulk coverage. `scripts/sync_narratives.py --limit 15 --skip-existing`. Local Ollama is CPU-bound, so keep batches small or switch to Groq/OpenAI for faster throughput.
- **Add local drift / monitoring history.** A baseline report exists, but each run overwrites the current metrics. Next step: persist timestamped metric snapshots and compare latest MAE/MAPE against previous runs.
- **Expand baseline model comparison.** A local baseline report now exists in `data/reports/baseline_comparison.md`, comparing the local seasonal-trend approach against seasonal-naive and moving averages. Next upgrade: add a scikit-learn/LightGBM baseline using the PySpark feature table.
- **Improve test coverage around operational flows.** `tests/` now covers API dashboard endpoints, ETL parsing, RAG formatting, local forecasting, local doctor, and narrative selection. Remaining gaps: pipeline orchestration, Streamlit query helpers, the new live-generation endpoint, and failure/interrupt paths.
- **Pin dependencies harder if needed.** `requirements.lock` exists for the current local runtime. A stronger future option would be `uv.lock` with platform-aware dependency resolution and a documented fresh-clone install path.

## Medium-term (new capability)

- **Real-time / incremental forecasting.** Current pipeline is a full weekly batch re-train. A streaming or incremental-update path (new day's actuals → adjust next-day forecast without full retrain) would be a meaningful upgrade for the "production-grade" framing.
- **Backend support for narrative generation jobs.** The CLI can safely generate and skip existing narratives now. A useful backend upgrade would expose a small job endpoint for "generate next N narratives" and job status polling, without adding auth yet.
- **Model monitoring / drift detection.** `bq/sql/evaluate_model.sql` computes ARIMA diagnostics once per training run; local baseline metrics exist but do not yet track drift over time or automated retrain triggers.
- **Multi-tenant / auth on the API.** `POST /v1/pipeline/run` uses a single shared secret header. A real deployment would want per-user auth (API keys, OAuth) rather than one static secret.
- **Alerting.** No notification path exists for pipeline failures (`pipeline_runs.status = 'failed'` just sits in the table). Slack/email webhook on failure would close the loop.

## Long-term (bigger bets)

- **Swap ARIMA_PLUS for a learned model.** BigQuery ML ARIMA_PLUS is convenient (zero infra, per-product auto-training) but a gradient-boosted or transformer-based forecaster (e.g. via Vertex AI, or a custom PyTorch/LightGBM model trained on the PySpark feature table) could likely beat it on MAPE, at the cost of infra complexity.
- **Multi-region / multi-currency support.** Dataset and pipeline are Rossmann-specific (Germany, EUR). Generalizing the schema to support arbitrary retailers/currencies would make this reusable beyond a portfolio demo.
- ~~Frontend beyond Streamlit.~~ **Done (2026-07-13).** Next.js 16 + Tailwind v4 dashboard and landing page now live in `frontend/`, consuming the FastAPI backend, with a custom Liquid Glass design system, D3 charts, and Spline 3D scenes. Streamlit remains available as a secondary internal BI tool.
- **Wire up the real GCP path end-to-end.** Everything in `etl/beam_pipeline.py` and `bq/sql/` is real, untouched code — just needs a GCP project, GCS bucket, and billing enabled to run for real. This is intentionally deferred while the non-GCP local/backend path is being strengthened.

## Explicitly out of scope (by design, not oversight)

- Fabricating git history / backdated commits to misrepresent development timeline — declined twice now (original session, and again 2026-07-13 when asked for a mechanical "30 commits, 2 files each" split and separately when a script file was twice modified outside the conversation to inject backdated timestamps). Not pursued as future work either. See `memory.md` → "Git hygiene this session" for details.
