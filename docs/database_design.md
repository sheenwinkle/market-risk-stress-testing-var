# Database Design

## Snapshot history

Risk, model, stress, control, efficiency, and Treasury outputs are append-only snapshots keyed by `run_id`. A repeated execution with the same input and configuration hashes deletes and rewrites only that run, making retries idempotent. A changed input or configuration creates a new run ID and preserves the prior result.

Large reusable market-data tables (`prices`, `asset_returns`, `portfolio_returns`, and `var_backtest`) are refreshed as current analytical datasets. Snapshot tables retain the decision and governance history without duplicating every source observation on each run.

Every snapshot table receives an index on `run_id`. PostgreSQL and SQLite use the same SQLAlchemy transaction boundary and reporting schema.

## Migration behaviour

Version 0.3 automatically replaces a legacy snapshot table once when it does not yet contain `run_id`. Subsequent runs use append/idempotent behaviour. This lightweight migration is suitable for the public demonstrator; a production platform should manage explicit schema revisions with Alembic or the employer's database change process.

## Integration test

The PostgreSQL integration test activates when `TEST_DATABASE_URL` is configured. It writes and queries a snapshot using the real PostgreSQL driver. Local SQLite tests independently verify retry idempotency, preservation of new runs, and current-table refresh behaviour.
