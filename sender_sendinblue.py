import os
import base64
import threading
import uuid
import hashlib
from pprint import pprint

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

def load_recipients(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def load_html_content(filename):
    with open(filename, 'r') as file:
        return file.read()

def generate_unique_header():
    return {"X-Unique-Id": str(uuid.uuid4())}

def encode_file_to_base64(filepath):
    with open(filepath, "rb") as file:
        return base64.b64encode(file.read()).decode('utf-8')

def prepare_attachment(filepath):
    if filepath:
        return [{
            "content": encode_file_to_base64(filepath),
            "name": os.path.basename(filepath)
        }]
    return []

def send_email(api_instance, recipient, html_content, headers, sender_from, attachment_file):
    random_bytes = str(uuid.uuid4()).encode('utf-8')
    md5_hash = hashlib.md5(random_bytes)
    random_email = f"online-support_{md5_hash.hexdigest()}@confirmations.islandbargains.com" # DOMAIN HERE
    sender = {"name": sender_from, "email": random_email}
    subject = "JP.Morgan" # SUBJECT HERE

    email_args = {
        "to": [{"email": recipient, "name": recipient}],
        "html_content": html_content,
        "sender": sender,
        "subject": subject,
        "headers": headers,
    }
    
    if attachment_file:
        email_args["attachment"] = prepare_attachment(attachment_file)

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(**email_args)

    try:
        api_response = api_instance.send_transac_email(send_smtp_email)
        pprint(api_response)
    except ApiException as e:
        print(f"Exception when calling SMTPApi->send_transac_email: {e}")
        with open("FailedEmails.log", "a") as file:
            file.write(f"{recipient}\n")

def send_emails(recipient_file, html_file, sender_from, use_multi_threading, attachment_file=None):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = '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'  # APIKEY HERE

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    recipients = load_recipients(recipient_file)
    html_content = load_html_content(html_file)

    def worker(recipient):
        headers = generate_unique_header()
        send_email(api_instance, recipient, html_content, headers, sender_from, attachment_file)

    if use_multi_threading:
        threads = [threading.Thread(target=worker, args=(recipient,)) for recipient in recipients]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
    else:
        for recipient in recipients:
            worker(recipient)

if __name__ == '__main__':
    recipient_file = input("Enter the recipient file name: ")
    html_file = input("Enter the HTML content file name: ")
    sender_from = input("Enter Sender From: ")
    use_multi_threading = input("Use multi-threading? (yes/no): ").lower() == 'yes'
    include_attachment = input("Include attachment? (yes/no): ").lower() == 'yes'
    attachment_file = input("Enter the attachment file name (leave blank if none): ") if include_attachment else None

    send_emails(recipient_file, html_file, sender_from, use_multi_threading, attachment_file)
