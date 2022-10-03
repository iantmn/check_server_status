import socket
from datetime import datetime
from email.mime.text import MIMEText
import smtplib
import atexit
import ssl

# #### VARIABLES #### #

# list of servers to check with the following items in the
# definitions per-server: ('hostname', 'ssl or plain', portnumber)
SERVER_LIST = [
    ("netw.nl", "ssl", 443),
    ("tiemann.nl", "ssl", 443),
    # ("tiemann-design.nl", "ssl", 443),
    ("code.tiemann.nl", "plain", 80),
    ("pbx.tiemann-design.nl", "ssl", 443),
    ]

# Globally define these lists as 'empty' for population later.
SRV_DOWN = []
SRV_UP = []

# Email handling items - email addresses
ADMIN_NOTIFY_LIST = ["an_email_address"]
FROM_ADDRESS = "no-reply@foo-bar-baz"

# Valid Priorities for Mail
LOW = 1
NORMAL = 2
HIGH = 3


# Begin Execution Here

@atexit.register
def _exit():
    print(f"{current_timestamp()} server Status Checker Now Exiting.")


def current_timestamp():
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")


def send_server_status_report():
    print("Sending email...")
    # Init priority - should be NORMAL for most cases, so init it to that.
    priority = NORMAL

    # Init the send_mail flag.  Ideally, we would be sending mail if this function is
    # called, but we need to make sure that there are cases where it's not necessary
    # such as when there are no offline servers.
    send_mail = True

    if len(SRV_UP) == 0:
        up_str = "Servers online: None!  ***THIS IS REALLY BAD!!!***"
        priority = HIGH
    else:
        up_str = f"Servers online: {SRV_UP}"

    if len(SRV_DOWN) == 0:
        down_str = "Servers down: None!"
        send_mail = False
    else:
        down_str = f"Servers down: {SRV_DOWN}   ***CHECK IF SERVERS LISTED ARE REALLY DOWN!***"
        priority = HIGH

    if len(SRV_UP) == len(SERVER_LIST) and len(SRV_DOWN) == 0:
        priority = LOW

    if send_mail:
        body = f"""Server Status Report - {current_timestamp()}

    {down_str}

    {up_str}"""

        # craft msg base
        msg = MIMEText(body)
        msg['Subject'] = f"Server Status Report - {current_timestamp()}"
        msg['From'] = FROM_ADDRESS
        msg['Sender'] = FROM_ADDRESS  # This is sort of important...

        if priority == LOW:
            # ThunderBird "Lowest", works with Exchange.
            msg['X-Priority'] = '5'
        elif priority == NORMAL:
            # Plain old "Normal". Works with Exchange.
            msg['X-Priority'] = 'Normal'
        elif priority == HIGH:
            # ThunderBird "Highest", works with Exchange.
            msg['X-Priority'] = '1'

        # Initialize SMTP session variable so it has the correct scope
        # within this function, rather than just inside the 'try' statement.
        smtp = None

        try:
            # SMTP is important, so configure it via Google Mail.
            smtp = smtplib.SMTP('smtp.gmail.com', 587)
            smtp.starttls()
            smtp.login(FROM_ADDRESS, 'ThePassword')
        except Exception as e:
            print(f"Could not correctly establish SMTP connection with Google, error was: {e.__str__()}")
            exit()

        for destaddr in ADMIN_NOTIFY_LIST:
            # Change 'to' field, so only one shows up in 'To' headers.
            msg['To'] = destaddr

            try:
                # Actually send the email.
                smtp.sendmail(FROM_ADDRESS, destaddr, msg.as_string())
                print(f"{current_timestamp()}  Status email sent to [{destaddr}]")
            except Exception as e:
                print(f"Could not send message, error was: {e.__str__()}")
                continue

        # No more emails, so close the SMTP connection!
        smtp.close()
        print("Email send!")
    else:
        print(f"{current_timestamp()}  All's good, do nothing")


def main():
    for (srv, mechanism, port) in sorted(SERVER_LIST):
        # [ 'serverhost' , 'ssl' or 'plain' ]
        print(f"{srv}, {mechanism}, {port}")

        try:
            if mechanism == 'plain':
                # Use a plain text connector for this.
                print(f"{current_timestamp()}  Using Plain for [{srv}]...")
                socket.create_connection((f"{srv}", port), timeout=10)
            elif mechanism == 'ssl':
                # We're going to use an SSL connector for this.
                print(f"{current_timestamp()}  Using SSL for [{srv}]...")
                ssl.wrap_socket(socket.create_connection((f"{srv}", port), timeout=10))
            else:
                print(f"{current_timestamp()}  Invalid mechanism defined for [{srv}], skipping...")
                continue
            SRV_UP.append(srv)
            print(f"{current_timestamp()}  {srv}: UP")
        except socket.timeout:
            SRV_DOWN.append(srv)
            print(f"{current_timestamp()}  {srv}: DOWN")
            continue
        except Exception as err:
            print(f"An error occurred: {err.__str__()}")
            exit()

    send_server_status_report()  # Create email to send the status notices.

    exit()  # Exit when done


if __name__ == "__main__":
    print(f"{current_timestamp()}  Server Status Checker Running....")
    main()