import socket
import ssl
from datetime import datetime


# CODE #

def current_timestamp():
    """Returns current date and time as a datetime object

    Returns:
        datetime object: datetime in format DD-MM-YYYY HH:MM:SS
    """
    return datetime.now().strftime("[%d-%m-%Y %H:%M:%S]")


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
                if entry[0] == "#" or entry[0] == "\n":
                    continue
                entry_list = entry.split(",")
                try:
                    server_list.append(
                        (entry_list[0].strip(), entry_list[1].strip(), entry_list[2].strip()))
                except IndexError:
                    raise IndexError(
                        "Value extraction from file failed. Make sure the file is structured properly.")
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
                ssl.wrap_socket(socket.create_connection(
                    (server, port), timeout=10))  # TODO: Deprecated method
            else:
                print(
                    f"{current_timestamp()} Invalid mechanism defined for [{server}], skipping...")

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


if __name__ == "__main__":
    # Run the server check.
    server_check("server_list.txt", mode="file")
