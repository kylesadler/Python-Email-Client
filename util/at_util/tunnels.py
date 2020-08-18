import pymongo
import os
import logging
import paramiko
from ftplib import FTP
from sshtunnel import SSHTunnelForwarder

class DBTunnel:

    def __init__(self, ip, bind_port, ssh_username, ssh_pkey):
        self.tunnel = SSHTunnelForwarder(
                (ip, 22),
                ssh_username=ssh_username,
                ssh_pkey=ssh_pkey, 
                remote_bind_address=('127.0.0.1', bind_port)
            )

        self.tunnel.start()


    def __del__(self): 
        self.close()

    def port(self):
        return self.tunnel.local_bind_port
    
    def close(self):
        try:
            self.tunnel.stop()
        except:
            pass


class MongoDBTunnel:

    def __init__(self, ip, ssh_username, ssh_pkey, mongo_user, mongo_pass, local=False):
        self.db_name = None
        self.local = local
        if self.local:
            self.client = pymongo.MongoClient('127.0.0.1', 27017)
        else:
            self.tunnel = DBTunnel(ip, 27017, ssh_username, ssh_pkey)
            self.client = pymongo.MongoClient('127.0.0.1', self.tunnel.port(), username=mongo_user, password=mongo_pass, authSource='admin')

    def collection(self):
        return self.client['scraper']['farms'] # for scraper

    def __getitem__(self, key):
        # key is 'prod' for farm value tool live production database
        # key is 'analytics' for data analytics
        # key is 'scraper' for scraper database
        # key is 'dev' for data processing and testing
        assert key in ('dev','prod','scraper','analytics', 'labeled', 'unlabeled') or self.local
        self.db_name = key
        return self.client[key]['farms'] 

    def __del__(self): 
        self.close()

    def close(self):
        try:
            self.client.close()
        except:
            pass

        try: 
            self.tunnel.close()
        except:
            pass
    
    def get_name():
        return self.db_name

class FTPTunnel:

    def __init__(self, ip, ssh_username, ssh_pkey):
        self.ssh = paramiko.SSHClient() 
        self.ssh.load_host_keys(ssh_pkey.split('id_rsa')[0]+'known_hosts')
        self.ssh.connect(ip, username=ssh_username, key_filename=ssh_pkey)
        self.sftp = self.ssh.open_sftp()

    def __del__(self): 
        self.close()

    def close(self):
        self.sftp.close()
        self.ssh.close()