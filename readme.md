# Llama Email bot

Simple email bot to host a Llama chatbot over email

## Usage Instructions

- Subject is `<model> <system prompt>`
    - where `<model>` is one of
        - `llama3`,
        - `llama3.1`,
        - `llama3.2`,
        - `llama2`,
        - `llama2-uncensored`,
        - `llama1`
    - and `<system prompt>` is anything you want.
- Body is your chat message to the bot. you can reply or simply send with the same subject line to continue the same
  chat
- A hosted instance is available at [llama@this-is-an-ai.lol](mailto:llama@this-is-an-ai.lol)

## Setup instructions

- install ollama library (i couldve just used the http endpoint to keep dependency free but lazy)
    - ex. `pip install ollama`
- create `login.json` with the following fields where
    - displayname is the displayname of the bot when sending emails
    - email is the email to send from
    - password is login password
    - smtp_addr, smtp_port, imap_addr, and imap_port are the respective addresses to reach the mail server
    - default_model is the ollama model that will be used if one is not specified
    - permitted_models is the models that the user is able to select. All of the models in this list should be pulled,
      ex. `ollama pull <model>`

```json
{
  "displayname": "Llama Chatbot",
  "email": "llama@this-is-an-ai.lol",
  "password": "[REDACTED]",
  "smtp_addr": "mail.pain.agency",
  "smtp_port": 465,
  "imap_addr": "mail.pain.agency",
  "imap_port": 993,
  "default_model": "llama3.2",
  "permitted_models": [
    "llama3",
    "llama3.1",
    "llama3.2",
    "llama2",
    "llama2-uncensored",
    "llama1"
  ]
}
```
