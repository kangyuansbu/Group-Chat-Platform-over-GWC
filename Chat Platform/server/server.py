import socket
import pickle
from threading import Thread
from socketserver import ThreadingMixIn
import ast
import time
from time import sleep

# Multithreaded Python server

# MASTER SERVER SETTINGS
TCP_IP = socket.gethostname()
TCP_PORT = 443
BUFFER_SIZE = 2048

# RELAY PROXY SERVER ADDRESSES
RELAY = ['35.189.127.126',
         '35.243.212.159']


# Multithreaded Python server
class ClientThread(Thread):
    def __init__(self,ip,port):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        print("[+] New server socket thread started for " + ip + ":" + str(port))

    def run(self):


        while True :
            data = conn.recv(2048)
            if len(data) > 0:


                msg = pickle.loads(data)
                print_msg(msg)
                reply_msg = Msg()
                reply_msg.relays = RELAY

                # -----------------------------------------
                # CLIENT PING
                # -----------------------------------------
                if msg.type == 0:
                    reply_msg.type = 0

                # -----------------------------------------
                # USER REGISTRATION
                # -----------------------------------------
                if msg.type == 1:
                    # New user registration, check duplicate USERNAME
                    if msg.username not in database.users:
                        database.users[msg.username] = msg.password
                        database.keys[msg.username] = msg.publickey
                        reply_msg.type = 0
                    else:
                        reply_msg.type = -1
                    print(database.users)

                # -----------------------------------------
                # USER AUTHENTICATION
                # -----------------------------------------
                if msg.type == 2:
                    # Check login information
                    if msg.username not in database.users:
                        # No such user
                        reply_msg.type = -1
                    else:
                        # Username exists
                        if msg.password != database.users[msg.username]:
                            # wrong password
                            reply_msg.type = -1
                        else:
                            # authentication passed!
                            reply_msg.type = 0
                            print("User authenticated.")


                # -----------------------------------------
                # PUBLIC KEY REQUEST
                # -----------------------------------------
                if msg.type == 3:
                    # Check target user information
                    if msg.target not in database.users:
                        # No such user
                        reply_msg.type = -1
                    else:
                        # return target user's public key
                        reply_msg.username = msg.target
                        reply_msg.publickey = database.keys[msg.target]
                        reply_msg.type = 0


                # -----------------------------------------
                # NEW MAIL FROM CLIENT
                # -----------------------------------------
                if msg.type == 4:
                    # Check login information
                    if msg.username not in database.users:
                        # No such user
                        reply_msg.type = -1
                    else:
                        # Username exists
                        if msg.password != database.users[msg.username]:
                            # wrong password
                            reply_msg.type = -1
                        else:
                            # authentication passed, store message content
                            mail_tmp = Mail()
                            mail_tmp.timestamp = time.time()
                            mail_tmp.sender = msg.username
                            mail_tmp.receiver = msg.target
                            mail_tmp.payload = msg.payload
                            if msg.target in database.messages:
                                database.messages[msg.target].append(mail_tmp)
                            else:
                                database.messages[msg.target] = [mail_tmp]

                            reply_msg.type = 0
                            print(database.messages)


                # -----------------------------------------
                # CLIENT RETRIVING MAIL FROM INBOX
                # -----------------------------------------
                if msg.type == 5:
                    # Check login information
                    if msg.username not in database.users:
                        # No such user
                        reply_msg.type = -1
                    else:
                        # Username exists
                        if msg.password != database.users[msg.username]:
                            # wrong password
                            reply_msg.type = -1
                        else:
                            # authentication passed, load inbox into payload
                            if msg.username in database.messages:
                                reply_msg.payload = database.messages[msg.username]
                            else:
                                reply_msg.payload = []
                            reply_msg.type = 0
                            print(database.messages)


                reply_msg_bytes = pickle.dumps(reply_msg)
                conn.send(reply_msg_bytes)  #echo

                # --------------------------------------------------
                # Consolidate current databse state and save locally
                # --------------------------------------------------
                #pickle.dump(database, open("server_database", "wb"))
                print("database updated.")
                print("Current users: ", len(database.users), "messages: ", len(database.messages))





# Message/header struct
# type -1 - NOT OK.
# type 0 - OK!
# type 1 - username registration
# type 2 - login authentication
# type 3 - request public key of a user
# type 4 - send encrypted message
class Msg:
    type = 0
    username = ""
    target = ""
    password = b""
    publickey = b""
    payload = b""
    relays = []

class Mail:
    timestamp = ""
    sender = ""
    receiver = ""
    payload = ""


class database:
    users = {}
    messages = {}
    keys = {}

'''
THIS IS FOR CREATING A NEW DATABASE
# Its important to use binary mode
dbfile = open('server_database', 'ab')
newdb = database()
# source, destination
pickle.dump(newdb, dbfile)
dbfile.close()
'''

# function for debugging purpose
def print_msg(msg):
    print("TYPE: ", msg.type)
    print("USERNAME: ", msg.username)
    print("PASSWORD: ", msg.password)


# load DATABASE
dbfile = open('server_database', 'rb')
database = pickle.load(dbfile)
dbfile.close()


tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tcpServer.bind((TCP_IP, TCP_PORT))
threads = []

# Open up listening ports for multiple connections
while True:
    tcpServer.listen(4)
    print("Multithreaded Python server : Waiting for connections from TCP clients...")
    (conn, (ip,port)) = tcpServer.accept()
    newthread = ClientThread(ip,port)
    newthread.start()
    threads.append(newthread)

for t in threads:
    t.join()
