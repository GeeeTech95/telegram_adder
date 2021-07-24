from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChannel
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError
from telethon.tl.functions.channels import InviteToChannelRequest
import csv
import traceback
import time
import sys
from logins import logins

Users_Added = 0
link = 't.me/joinchat/RyHbZrUzf-1YMMtE'


auth_username = input("Enter users who's login details you want to use  :  ")
auth_user = logins.get(auth_username,None)
if not auth_user :
    print("The entered username does not exist,please crosscheck")
    exit()
no_to_add = input("How many users do you want to add  : ")
no_to_add = int(no_to_add)
api_id = auth_user['api_id']
api_hash = auth_user['api_hash']
phone = auth_user['phone']
client = TelegramClient(phone, api_id, api_hash)

client.connect()

if not client.is_user_authorized():
    client.send_code_request(phone)
    client.sign_in(phone, input('Enter the code: '))

input_file = input("Enter name of csv file to add from : ")
users = []

with open(input_file, encoding='UTF-8') as f:
    rows = csv.reader(f, delimiter=",", lineterminator="\n")
    next(rows, None)
    for row in rows:
        user = {}
        user['username'] = row[0]
        user['id'] = int(row[1])
        user['access_hash'] = int(row[2])
        user['name'] = row[3]
        users.append(user)

chats = []
last_date = None
chunk_size = 200
groups = []

result = client(GetDialogsRequest(
    offset_date=last_date,
    offset_id=0,
    offset_peer=InputPeerEmpty(),
    limit=chunk_size,
    hash=0
))
chats.extend(result.chats)

for chat in chats:
    try:
        if chat.megagroup == True:
            groups.append(chat)
    except:
        continue

print('Choose a group to add members:')
i = 0
for group in groups:
    print(str(i) + '- ' + group.title)
    i += 1

g_index = input("Enter a Number: ")
target_group = groups[int(g_index)]

target_group_entity = InputPeerChannel(target_group.id, target_group.access_hash)

mode = int(1)



for user in users:
    try:
        print("Adding {}".format(user['id']))
        if mode == 1:
            if user['username'] == "":
                continue
            user_to_add = client.get_input_entity(user['username'])

        client(InviteToChannelRequest(target_group_entity, [user_to_add]))
        #time.sleep(1)
        Users_Added += 1

        if Users_Added == no_to_add : 
            print("Added {} members,exiting ..".format(Users_Added))
            break
    except PeerFloodError:
        print("Getting Flood Error from telegram. Script is stopping now. Please try again after some time.")
        #time.sleep(10)
    except UserPrivacyRestrictedError:
        print("The user's privacy settings do not allow you to do this. Skipping.")
        #time.sleep(5)
    except:
        traceback.print_exc()
        print("Unexpected Error")
        #time.sleep(5)
        continue
