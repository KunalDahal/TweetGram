# Command Reference

`/acc -a <username> <password> <email> <email_password> [proxy]`

Create an account using credentials.

`/acc -c <username> <auth_token> <ct0> [proxy]`

Create an account using cookies.

`/acc -r <account_id>`

Remove an account and related data.

`/acc -l <twitter_list_id> -a <account_id>`

Assign a Twitter/X List and capture its baseline.

`/acc -l <twitter_list_id> -r <account_id>`

Remove a list assignment and cancel pending jobs.

`/acc -i <account_id>`

Activate an account worker.

`/acc -h <account_id>`

Halt an account worker.

`/acc -p <account_id> -a <proxy>`

Add an account proxy.

`/acc -p <account_id> -r <proxy>`

Remove an account proxy.

`/acc <account_id> -ka <llm_key>`

Add or replace an account LLM key.

`/acc <account_id> -kr <llm_key>`

Remove an account LLM key after fingerprint verification.

`/acc <account_id> -lm <provider> <model>`

Set the account LLM provider and model.

`/acc -s`

Show status for all accounts.

`/prompt "<text>"`

Update the global prompt and increment the prompt version.
