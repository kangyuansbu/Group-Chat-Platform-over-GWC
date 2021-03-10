# Python TCP Client
import socket
import pickle
import hashlib
from Crypto.PublicKey import RSA
from Crypto import Random
from Crypto.Cipher import PKCS1_OAEP
import ast
from os import path

default_relay = '35.189.127.126'
port = 443
BUFFER_SIZE = 8192

class Session:
    username = ""
    password = b""
    keypair = b""
    conn = ""
    relays = ['35.189.127.126',
             '35.243.212.159']

def log(msg):
    print(bcolors.OKBLUE + " - " +  msg + bcolors.ENDC)

def err(msg):
    print(bcolors.FAIL + " - " +  msg + bcolors.ENDC)

def seg():
    print("-" * 50)

# Prompt for input
def prompt(msg):
    print(bcolors.WARNING + msg + bcolors.ENDC)
    seg()
    i = input()
    seg()
    return i

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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







# function for debugging purpose
def print_msg(msg):
    print("TYPE: ", msg.type)
    print("USERNAME: ", msg.username)
    print("PASSWORD: ", msg.password)


def conn_init(session):
    session.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 3 seconds connection timeout
    session.conn.settimeout(3.0)

    try:
        # Default relay
        log("Connecting to default relay server...")
        session.conn.connect((default_relay, port))
        return default_relay

    except:
        # Our first relay server is down, go down the relay server list
        err("Default relay server is down!")
        for i in range(len(session.relays)):
            try:
                log("Trying relay server at " + session.relays[i] + "...")
                session.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                session.conn.settimeout(5.0)
                session.conn.connect((session.relays[i], port))
                return session.relays[i]
                break
            except:
                err("Relay server at " + session.relays[i] + " is down. Trying a new one...")


def conn_close(session):
    session.conn.close()


def send_mail(session):
    conn_init(session)

    # 1. Get public key of the target user.
    target = prompt("Who do you want to send to?")
    new_msg = Msg()
    new_msg.type = 3
    new_msg.target = target
    MESSAGE = pickle.dumps(new_msg)
    log("Requesting public key...")
    session.conn.send(MESSAGE)
    data = session.conn.recv(BUFFER_SIZE)
    recv_msg = pickle.loads(data)
    if recv_msg.type != 0:
        # Getting public key Unsuccessful
        err("Getting public key Unsuccessful!")
        return -1

    target_publickey = RSA.importKey(recv_msg.publickey)

    # 2. Encrypt text message
    text = prompt("What do you want to say?").encode()
    log("Encrypting your message...")

    encryptor = PKCS1_OAEP.new(target_publickey)
    encrypted = encryptor.encrypt(text)

    # 3. Send message to server along with credentials
    new_msg = Msg()
    new_msg.type = 4
    new_msg.username = session.username
    new_msg.password = session.password
    new_msg.target = target
    new_msg.payload = encrypted
    MESSAGE = pickle.dumps(new_msg)
    session.conn.send(MESSAGE)
    data = session.conn.recv(BUFFER_SIZE)

    conn_close(session)

    recv_msg = pickle.loads(data)
    if recv_msg.type != 0:
        # send message failed
        err("Sending new message unsuccessful!")
        return -1
    log("Congrats! New message is sent securely.")


def retrieve_mail(session):
    # 1. send my credentials to server to retrieve mail
    conn_init(session)
    log("Contacting server for your inbox...")
    new_msg = Msg()
    new_msg.type = 5
    new_msg.username = session.username
    new_msg.password = session.password
    MESSAGE = pickle.dumps(new_msg)
    session.conn.send(MESSAGE)
    data = session.conn.recv(BUFFER_SIZE)
    session.conn.close()

    # 2. process retrieved information
    recv_msg = pickle.loads(data)



    if recv_msg.type != 0:
        # send message failed
        log("Retrieving new message unsuccessful!")
        return -1

    if len(recv_msg.payload) > 0:
        log("Message(s) retrieved, decrypting...")
        seg()
        for item in recv_msg.payload:
            print("[Sender]    " + item.sender)
            print("[Timestamp] " + str(item.timestamp))
            print("[Message]   ")
            decryptor = PKCS1_OAEP.new(session.keypair)
            decrypted_data = decryptor.decrypt(ast.literal_eval(str(item.payload)))
            print(decrypted_data.decode())
            seg()

    else:
        log("You have no messages in your inbox.")






def new_user(session):
    conn_init(session)

    username = prompt("What do you want to be called? letters and numbers only.")
    password = prompt("Your password?")

    # hash password into MD5 format
    password = hashlib.md5(password.encode()).digest()

    # generate public/private key pair
    log("Generating key pairs...")
    random_generator = Random.new().read
    key = RSA.generate(2048, random_generator) #generate pub and priv key

    # Create a message and convert into bytes
    new_msg = Msg()
    new_msg.type = 1
    new_msg.username = username
    new_msg.password = password
    new_msg.publickey = key.publickey().exportKey()
    MESSAGE = pickle.dumps(new_msg)

    log("Contacting server...")
    session.conn.send(MESSAGE)
    data = session.conn.recv(BUFFER_SIZE)
    recv_msg = pickle.loads(data)

    session.conn.close()

    if recv_msg.type == 0:
        log("Successful registration!")
        session.username = username
        session.password = password

        # Save key pair locally for next login
        with open("pem/" + username + ".pem", "w") as prv_file:
            print(key.exportKey().decode(), file=prv_file)

        rsa_key = RSA.importKey(open("pem/" + username + ".pem", "rb").read())
        session.keypair = rsa_key

        return 0
    else:
        err("Unsuccessful registration")
        return -1



def login(session):
    username = prompt("Username?")
    password = prompt("Password?")

    # check if keypair is locally stored
    if path.isfile("pem/" + username + ".pem") == 0:
        err("No local private key is found.")
        return -1

    rsa_key = RSA.importKey(open("pem/" + username + ".pem", "rb").read())


    # hash password into MD5 format
    password = hashlib.md5(password.encode()).digest()

    # Create a message and convert into bytes
    new_msg = Msg()
    new_msg.type = 2
    new_msg.username = username
    new_msg.password = password
    MESSAGE = pickle.dumps(new_msg)

    conn_init(session)
    log("Contacting server...")
    session.conn.send(MESSAGE)
    data = session.conn.recv(BUFFER_SIZE)
    session.conn.close()
    recv_msg = pickle.loads(data)

    if recv_msg.type == 0:
        log("Successful Login!")
        session.username = username
        session.password = password
        session.keypair = rsa_key
        return 0
    else:
        err("Unsuccessful Login")
        return -1

def main_menu(session):
    seg()
    print("Welcome! You can now send or receive messages.")
    seg()
    log("You are now logged in as " + session.username)
    seg()
    choose = input("1 new message \n2 check my inbox \n").strip()
    seg()
    while choose == "1" or choose == "2":
        if choose == "1":
            send_mail(session)
        if choose == "2":
            retrieve_mail(session)
        seg()
        choose = input("1 new message \n2 check my inbox \n").strip()
        seg()


def ping_server(session):
    relay_addr = conn_init(session)
    new_msg = Msg()
    new_msg.type = 0
    session.conn.send(pickle.dumps(new_msg))
    data = session.conn.recv(BUFFER_SIZE)
    recv_msg = pickle.loads(data)
    if recv_msg.type != 0:
        err("Unable to reach master server via relay server.")
    log("Master server reachable via relay servers.")
    log("Relay server addresses updated.")
    conn_close(session)

def main():
    seg()
    session = Session()
    ping_server(session)
    log("Welcome to your secure chat app. type in a number to continue")
    seg()
    choose = prompt("1 new user registration \n2 log into existing user").strip()
    seg()
    if choose == "1":
        if new_user(session) == -1:
            return -1
        else:
            main_menu(session)
    if choose == "2":
        if login(session) == -1:
            return -1
        else:
            main_menu(session)

main()




'''

#SAMPLE ENCRYPTION/DECRYPTION CODE

import Crypto
from Crypto.PublicKey import RSA
from Crypto import Random
import ast

random_generator = Random.new().read
key = RSA.generate(1024, random_generator) #generate pub and priv key

publickey = key.publickey() # pub key export for exchange

encrypted = publickey.encrypt('encrypt this message', 32)
#message to encrypt is in the above line 'encrypt this message'

print 'encrypted message:', encrypted #ciphertext
f = open ('encryption.txt', 'w')
f.write(str(encrypted)) #write ciphertext to file
f.close()

#decrypted code below

f = open('encryption.txt', 'r')
message = f.read()


decrypted = key.decrypt(ast.literal_eval(str(encrypted)))

print 'decrypted', decrypted

f = open ('encryption.txt', 'w')
f.write(str(message))
f.write(str(decrypted))
f.close()
'''
