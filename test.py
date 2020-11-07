from pprint import pprint
from getpass import getpass

from pymail import Gmail, Outlook


def main():
    username = input("Enter username: ")
    password = getpass("Enter password for " + username + ": ")
    gmail = Gmail(username, password, testing=True)

if __name__ == '__main__':
    main()