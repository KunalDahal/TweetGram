# Operations Runbook

Use `/acc -s` to inspect configured accounts, list assignments, worker state, LLM configuration, and recent logs.

Common actions:

- Halt a worker before rotating credentials: `/acc -h <account_id>`
- Update LLM provider/model: `/acc <account_id> -lm <provider> <model>`
- Replace LLM key: `/acc <account_id> -ka <llm_key>`
- Resume after fixing an account: `/acc -i <account_id>`

Secrets are never returned in Telegram responses.
