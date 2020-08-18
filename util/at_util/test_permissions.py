# tests permissions of all database users using the current server's login information

from db import test_permissions

ip = "x.x.x.x"
ssh_user = "x"
ssh_pkey = "/path/to/pkey"
auths = [
    ("user1","pass1"),
    ("user2","pass2"),
    ("userN","passN"),
]
collections = ('col1','col2','colN')

test_permissions(ip, ssh_user, ssh_pkey, auths, collections)