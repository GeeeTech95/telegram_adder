from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChannel
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError
from telethon.tl.functions.channels import InviteToChannelRequest
import csv
import traceback
import time
import sys
import json
from core import logins,csv_list

def reset_offset_file() :
    #we can choose to delete
    pass


def get_users(input_csv,offset_file = None,reset_offset = False,group_title = None) :
    """ offset file is a json file containing the last indexes of the last read"""
    """ consider offset tells if we should clear the offset file
    group title is used to obtain last offset for a particular group"""
    
    if not reset_offset :
        try :
            with open(offset_file,'r') as jf :
                data = json.load(jf)
                #dictionary of csv filenames and last offsets
                offset_dicts = {}
                for file_name,line_index in data['group_title'] :
                    offset_dicts[file_name]  = line_index
        except FileNotFoundError :
            print("offset file does not exist.")
            print()
            print("negelecting,setting reset_offset to True")
            reset_offset = True
    else :
        #we now reset offset files 
        reset_offset_file()


    users  = []
    users_list = []
    #to update offset file
    new_offset_file_content = {}
    new_offset_list = []
    for _csv in input_csv :
        new_offset_data = {}
        with open(_csv, encoding='UTF-8') as f  :
            rows = csv.reader(f, delimiter=",", lineterminator="\n")
            next(rows, None)
            line_index = 0 #indexing the line read to save to offset incase
            for row in rows:
                user = {}
                user['username'] = row[0]
                user['id'] = int(row[1])
                user['access_hash'] = int(row[2])
                user['name'] = row[3]
                #consider from offset if it is allowed
                if not reset_offset :
                    #append users only from row greater than offset
                    if line_index > int(offset_dicts[_csv]) :
                        users.append(user)
                    else :
                        continue    
                else :
                    users.append(user)        
                line_index += 1

        users_list.append(users)
        new_offset_data[_csv] = line_index
       
        #append new file data
        new_offset_list.append(new_offset_data)
    #update only the group title for the 
    data[group_title] = new_offset_list
    #update offset file to new csv line index
    with open(offset_file,'w') as jf :
        jf.write(json.dump(data))
    return users_list        



def get_clients(add_no) :

    if add_no <= 100 :
        auth_username = input("Enter users who's login details you want to use  :  ")
        auth_user = logins.get(auth_username,None)
        if not auth_user :
            
            return None,None
        add_no = input("How many users do you want to add  : ")
        add_no = int(add_no)
        api_id = auth_user['api_id']
        api_hash = auth_user['api_hash']
        phone = auth_user['phone']
        client = TelegramClient(phone, api_id, api_hash)
        return (client,"single")


    elif add_no > 100 and add_no <= 1000 :    
        no_client  =  add_no//100
        added_clients  = 0
        clients = []
        offset = add_no - (no_client * 100)
        if offset < 0 : no_client += 1
        for _user in logins.keys() :
            auth_user = logins[_user]
            api_id = auth_user['api_id']
            api_hash = auth_user['api_hash']
            phone = auth_user['phone']
            client = TelegramClient(phone, api_id, api_hash)
            setattr(client,'auth_phone', phone)
            if added_clients == no_client :
                break
            clients.append(client) 
            added_clients += 1   
        return (clients,"multiple")    


def add_users(client,users,group = None) :
    #print("Adding members for ")
    current_add = 0
    client.connect()
    if not client.is_user_authorized():
        client.send_code_request(client.auth_phone)
        client.sign_in(client.auth_phone, input('Enter the code: '))

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
    #allow group selection done once
    if not group :     
        print('Choose a group to add members:')
        i = 0
        for group in groups:
            print(str(i) + '- ' + group.title)
            i += 1

        g_index = input("Enter a Number: ")
        target_group = groups[int(g_index)]
    
    else : target_group = group
    
    
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
            current_add += 1
            
            if Users_Added == add_no : 
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
    print("Added {} members".format(current_add))
    return target_group





def main() :
    Users_Added = 0
    link = 't.me/joinchat/RyHbZrUzf-1YMMtE'
    add_no = input("How many users do you want to add  : ")
    add_no = int(add_no)
    clients,nature = get_clients(add_no)
    if not clients : print("The entered username does not exist,please crosscheck")
    if nature == "single" :
        pass

    elif nature == "multiple" :
        group = None
        for client,users in zip(clients,get_users(csv_list,offset_file='offset_file.json')) :
            if not group :
                group = add_users(client, users)
            else : 
                add_users(client, users, group)    
    














if __name__ == "__main__" : main()