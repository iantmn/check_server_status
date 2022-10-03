import socket
from datetime import datetime
from email.mime.text import MIMEText
import smtplib
import atexit
import ssl

# #### VARIABLES #### #

# list of servers to check with the following items in the
# definitions per-server: ('hostname', 'ssl or plain', portnumber)
server_list = [
    ("tiemann.nl", "ssl", 443),
    # ("tiemann-design.nl", "ssl", 443),
    ]

# Globally define these lists as 'empty' for population later.
server_down = []
server_up = []

# Email handling items - email addresses
Notify_list = ["an_email_address"]
from_address = "no-reply@foo-bar-baz"

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

    if len(server_up) == 0:
        up_str = "Servers online: None!  ***THIS IS REALLY BAD!!!***"
        priority = HIGH
    else:
        up_str = f"Servers online: {server_up}"

    if len(server_down) == 0:
        down_str = "Servers down: None!"
        send_mail = False
    else:
        down_str = f"Servers down: {server_down}   ***CHECK IF SERVERS LISTED ARE REALLY DOWN!***"
        priority = HIGH

    if len(server_up) == len(server_list) and len(server_down) == 0:
        priority = LOW

    if send_mail:
        body = f"""Server Status Report - {current_timestamp()}

    {down_str}

    {up_str}"""

        # craft msg base
        msg = MIMEText(body)
        msg['Subject'] = f"Server Status Report - {current_timestamp()}"
        msg['From'] = from_address
        msg['Sender'] = from_address  # This is sort of important...

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
            smtp.login(from_address, 'ThePassword')
        except Exception as e:
            print(f"Could not correctly establish SMTP connection with Google, error was: {e}")
            exit()

        for destaddr in Notify_list:
            # Change 'to' field, so only one shows up in 'To' headers.
            msg['To'] = destaddr

            try:
                # Actually send the email.
                smtp.sendmail(from_address, destaddr, msg.as_string())
                print(f"{current_timestamp()}  Status email sent to [{destaddr}]")
            except Exception as e:
                print(f"Could not send message, error was: {e.__str__()}")
                continue

        # No more emails, so close the SMTP connection!
        smtp.close()
        print("Email send!")
    else:
        print(f"{current_timestamp()}  All's good, do nothing")

def server_check(server_list_or_file: list[tuple[str, str, int]] | str, mode="list"):
    """Check the status of the servers in the list

    Args: server_list_or_file (list | file):    list of tuples containing the server name, method (plain or ssl) and the
                                                port or a file to the same information
    """

    print(f"{current_timestamp()}  Server Status Checker Running....")

    # code that transfers server_list_or_file to a list form if the input was a file
    if mode == "file":
        with open(server_list_or_file) as f:
            server_list = []
            for entry in f:
                if entry[0] == "#":
                    continue
                entry_list = entry.split(",")
                try:
                    server_list.append((entry_list[0].strip(), entry_list[1].strip(), entry_list[2].strip()))
                except IndexError:
                    raise IndexError("Value extraction from file failed. Make sure the file is structured properly.")
    # code that renames server_list_or_file to server_list
    elif mode == "list":
        server_list = server_list_or_file
    else:
        raise TypeError(f"{mode} is not a valid argument for mode.")

    # empty lists to store the results
    server_down = []
    server_up = []

    for (server, method, port) in server_list:
        # [ 'server' , 'ssl' or 'plain', 'port' ]
        print(f"{current_timestamp()} checking {server}, {method}, {port}")

        try:
            if method == 'plain':
                # Use a plain text connector for this.
                print(f"{current_timestamp()} Using Plain for [{server}]...")
                socket.create_connection((server, port), timeout=10)
            elif method == 'ssl':
                # We're going to use an SSL connector for this.
                print(f"{current_timestamp()} Using SSL for [{server}]...")
                ssl.wrap_socket(socket.create_connection((server, port), timeout=10))  # TODO: Deprecated method
            else:
                print(f"{current_timestamp()} Invalid mechanism defined for [{server}], skipping...")

            server_up.append(server)
            print(f"{current_timestamp()} {server}: UP")

        except socket.timeout:
            server_down.append(server)
            print(f"{current_timestamp()} {server}: DOWN")

        except Exception as err:
            server_down.append(server)
            print(f"An error occurred: {err}")

    with open("server_status.txt", "a") as f:
        if len(server_down) > 0:
            f.write(f"{current_timestamp()} servers down: {server_down}\n")
            print(f"{current_timestamp()} servers down: {server_down}")
        else:
            f.write(f"{current_timestamp()} all servers up!\n")
            print(f"{current_timestamp()} all servers up!")

    print(f"{current_timestamp()} server Status Checker Now Exiting.")



def main():
    for (srv, mechanism, port) in sorted(server_list):
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
            server_up.append(srv)
            print(f"{current_timestamp()}  {srv}: UP")
        except socket.timeout:
            server_down.append(srv)
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