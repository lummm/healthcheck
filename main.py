#!/usr/bin/env python3

import json
import os
import time
from typing import NamedTuple

import requests


class _ENV(NamedTuple):
    CHECK_ENDPOINT = os.environ["CHECK_ENDPOINT"]
    HEARTBEAT_S = int(os.environ.get("HEARTBEAT_S", "300"))
    SENDGRID_KEY = os.environ["SENDGRID_KEY"]
    TO_EMAIL = os.environ["TO_EMAIL"]
    FROM_EMAIL = os.environ["FROM_EMAIL"]


ENV = _ENV()


def send_mail(
        from_email: str,
        to_email: str,
        subject: str = "",
        body: str = "",
) -> None:
    print("sending mail to", to_email)
    url = "https://api.sendgrid.com/v3/mail/send"
    with requests.Session() as s:
        s.headers["authorization"] = f"Bearer {ENV.SENDGRID_KEY}"
        s.headers["content-type"] = "application/json"
        r = s.post(url, data=json.dumps({
            "personalizations": [
                {
                    "to": [{"email": to_email}]}
            ],
            "from": {
                "email": from_email,
            },
            "subject": subject,
            "content": [
                {
                    "type": "text/html",
                    "value": f"""
                    {body}
                    """,
                }
            ]
        }))
        if not r.ok:
            print("sending email failed: ", r.text)
        return r
    return


def send_enter_alarm_email():
    return send_mail(
        ENV.FROM_EMAIL,
        ENV.TO_EMAIL,
        subject="Endpoint is down",
        body="Target in alarm: " + ENV.CHECK_ENDPOINT,
    )


def send_exit_alarm_email():
    return send_mail(
        ENV.FROM_EMAIL,
        ENV.TO_EMAIL,
        subject="Endpoint is back online",
        body="Target: " + ENV.CHECK_ENDPOINT,
    )


def is_target_online():
    with requests.Session() as s:
        r = s.get(ENV.CHECK_ENDPOINT)
        return r.ok
    return


def main():
    in_alarm = False
    while True:
        if not is_target_online():
            print("DOWN")
            if not in_alarm:
                in_alarm = True
                send_enter_alarm_email()
        else:
            print("OK")
            if in_alarm:
                in_alarm = False
                send_exit_alarm_email()
        time.sleep(ENV.HEARTBEAT_S)
    return


if __name__ == '__main__':
    main()
