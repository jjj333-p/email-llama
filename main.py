import base64
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import imaplib
import email
from time import sleep
from ollama import chat
from ollama import ChatResponse

# directory to store message history
if not os.path.exists('./db/'):
    os.mkdir('./db/')

# Email details
with open("login.json", "r") as file:
    login = json.load(file)

run: int = 0

while True:
    print("run", run)
    run += 1

    try:
        # Connect to the server
        mail = imaplib.IMAP4_SSL(login["imap_addr"], login["imap_port"])
        mail.login(login["email"].split("@")[0], login["password"])

        # Select the mailbox you want to use
        mail.select("INBOX")

        # Search for new emails
        status, messages = mail.search(None, "UNSEEN")
        email_ids = messages[0].split()

        # fetch email ids we just searched for
        for num in email_ids:
            typ, data = mail.fetch(num, '(RFC822)')

            # no idea why a message id returns a list but okay
            for response in data:

                # everything does this, i have no idea
                if isinstance(response, tuple):
                    msg = email.message_from_bytes(response[1])
                    print("Subject:", msg['Subject'])
                    print("From:", msg['From'])
                    print("To:", msg['To'])
                    print("Date:", msg['Date'])
                    body: str = ""

                    # for some reason emails sent from gmail and such are in parts on the server
                    # and you have to fetch each part
                    if msg.is_multipart():
                        for part in msg.walk():
                            body += str(part.get_payload()[0])
                    else:
                        body = str(msg.get_payload())

                    filtering_body: list[str] = []
                    filtered_body: str = None
                    for line in body.splitlines():

                        # filter out quoted reply, rely on stored copy
                        if login["displayname"].split(" ")[0] in line or login["email"] in line:
                            filtered_body = "\n".join(filtering_body[:-1])
                            break
                        else:
                            filtering_body.append(line)

                    # if there never was any quoted body we have nothing to filter out
                    if filtered_body is None:
                        filtered_body = "\n".join(filtering_body[:])

                    subject_by_words: list[str] = msg['Subject'].split(" ")

                    # messages will be stored by base64 hash of subject
                    if subject_by_words[0] == "Re:" or subject_by_words[0] == "re:" or subject_by_words[0] == "RE:":
                        del subject_by_words[0]
                    encoded: str = base64.urlsafe_b64encode(
                        f'{msg["From"]} {" ".join(subject_by_words)}'.encode()).decode()

                    # attempt to parse out what model to use
                    model: str = login["default_model"]
                    default_model: bool = True
                    if subject_by_words[0] in login["permitted_models"]:
                        model = subject_by_words[0]
                        default_model = False
                        del subject_by_words[0]

                    system_prompt: dict[str, str] = {
                        "role": "system",
                        "content": " ".join(subject_by_words),
                    }
                    history: list[dict[str, str]] = [system_prompt]

                    # read in history from disk
                    if os.path.exists(f'./db/{encoded}.json'):
                        with open(f'./db/{encoded}.json', 'r') as file:
                            json_data = json.load(file)
                            for i, entry in enumerate(json_data):

                                # first item is duplicate system prompt
                                if i == 0:
                                    continue

                                history.append(entry)

                    # add latest user prompt
                    history.append({
                        "role": "user",
                        "content": filtered_body
                    })

                    # compute response
                    response: str = ""
                    try:
                        cr: ChatResponse = chat(model=model, messages=history)
                        response = cr.message.content
                    except Exception as e:
                        response = str(e)

                    # parse out relevant model
                    response_body: str = f''
                    if default_model:
                        response_body = f'{subject_by_words[0]} not a permitted model, using default model {model}.\n\n'
                    response_body += response

                    # create email object
                    response_message = MIMEMultipart()
                    response_message["From"] = login["email"]
                    response_message["To"] = msg["From"]
                    response_message["Subject"] = msg["Subject"] if msg["Subject"].startswith(
                        "Re:") else f"Re:{msg['Subject']}"
                    response_message.attach(MIMEText(response_body, "plain"))

                    # send email
                    try:
                        with smtplib.SMTP_SSL(login["smtp_addr"], login["smtp_port"]) as server:
                            server.login(login["email"].split('@')[0], login["password"])
                            server.send_message(response_message)
                        print("Email sent successfully!")
                    except Exception as e:
                        print(f"Error: {e}")

                    history.append({
                        "role": "assistant",
                        "content": response,
                    })

                    with open(f'./db/{encoded}.json', 'w', encoding="utf-8") as file:
                        json.dump(history, file, indent=4)

        mail.logout()
    except Exception as e:
        print(f"Error: {e}")

    # stop from raping my poor vps
    # stalwart is light, but it needs all the help it can get
    sleep(30)
