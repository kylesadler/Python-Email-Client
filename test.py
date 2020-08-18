from pprint import pprint
from getpass import getpass

from pymail import Gmail


def main():
    username = input("Enter username: ")
    password = getpass("Enter password for " + username + ": ")
    gmail = Gmail(username, password, testing=True)
    # gmail = Gmail(testing=False, username='farmers@acretrader.com', password=getpass())

if __name__ == '__main__':
    main()