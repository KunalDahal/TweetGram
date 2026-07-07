HELP_MESSAGE = """TweetGramBot commands:

/acc -a <username> <password> <email> <email_password> [proxy]
/acc -c <username> <auth_token> <ct0> [proxy]
/acc <account_id> -c <auth_token> <ct0> [proxy]
/acc -r <account_id>
/acc -l <twitter_list_id> -a <account_id>
/acc -l <twitter_list_id> -r <account_id>
/acc -i <account_id>
/acc -h <account_id>
/acc -p <account_id> -a <proxy>
/acc -p <account_id> -r <proxy>
/acc <account_id> -ka <llm_key>
/acc <account_id> -kr <llm_key>
/acc <account_id> -lm
/acc -s
/prompt "<text>"

Use /acc -s to check account status."""
