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

def get_offset_data(offset_file = None,group_title = None) :
    skip_offset  = False
    group_not_found = False
    """ offset file is a json file containing the last indexes of the last read"""
    """ consider offset tells if we should clear the offset file
    group title is used to obtain last offset for a particular group
    skip offset used for checking if csv read will take note of offset
    returns (skip_offset,group_not_found,offset_data)
    """
    try :
        with open(offset_file,'r') as jf :

            data = json.load(jf)
            #dictionary of csv filenames and last offsets
            offset_dicts = {}
            item = data.get('group_title',None)
            if item :
                for file_name,line_index in item.items() :
                    offset_dicts[file_name]  = line_index
                return (skip_offset,group_not_found,offset_dicts)

            else :
                print("{} not was not found in the offset file")
                print()
                print("assuming its the first adding to {}".format(group_title))
                skip_offset  = True
                group_not_found = True
                return (skip_offset,group_not_found,None)

    except FileNotFoundError :
        print("offset file does not exist.")
        print()
        print("assuming its the first adding to {}".format(group_title))
        print()
        skip_offset  = True
        return (skip_offset,group_not_found,None)



def get_users(input_csv,add_no) :
    if not add_no > 100 and not add_no <= 1000 :    
        print("only maximum of 1000 can go ata time")
        exit()
    no_users =  add_no//100
    added_users = 0
    users  = []
    users_list = []
    offset = add_no - (no_users * 100)
    if offset > 0 : no_users += 1
    #to update offset file
    new_offset_file_content = {}
    new_offset_list = []
    for _csv in input_csv :
        if added_users == no_users : break
        new_offset_data = {}
        with open(_csv, encoding='UTF-8') as f  :
            rows = csv.reader(f, delimiter=",", lineterminator="\n")
            next(rows, None)
            for row in rows:
                user = {}
                user['username'] = row[0]
                user['id'] = int(row[1])
                user['access_hash'] = int(row[2])
                user['name'] = row[3]
                users.append(user)              

        users_list.append(users)
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
        if offset > 0 : no_client += 1
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

def get_group(client) :
    """ uses one client instance to get group title used for whole exercise"""
    print("connecting...")
    client.connect()
    if not client.is_user_authorized():
        print("not authenticated,sending code....")
        client.send_code_request(client.auth_phone)
        
        client.sign_in(client.auth_phone, input('Enter the code: '))
        print("signinin...")
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
            #remember to add if chat.megagroup == True
            if  chat.megagroup == True :
                groups.append(chat)
        except:
            continue  
    #allow group selection done once
    print('Choose a group to add members:')
    i = 0
    for group in groups:
        print(str(i) + '- ' + group.title)
        i += 1

    g_index = input("Enter a Number: ")
    target_group = groups[int(g_index)]
    
    return target_group


def add_users(client,users,target_group,csv_list,skip_offset,grp_not_found,data_list) :
    global active_client
    print("Adding members for {} by client {}".format(target_group.title,active_client))
    current_add = 0
    
    new_data_list = []  #list of offset data for a group
    json_data = []   #json data
    line_index = 0 #initiaize line count
    target_group_entity = InputPeerChannel(target_group.id, target_group.access_hash)
    mode = int(1)  
    add_limit = 0 #add limit
    for user in users:
        if add_limit == 100 :
            print("reached 100 safe limit for cient {}".format(active_client))
            break
        try:
            print("Adding {}".format(user['id']))
            if mode == 1:
                if user['username'] == "":
                    continue
                user_to_add = client.get_input_entity(user['username'])
                
                #consider from offset if it is allowed
                if not skip_offset  :
                    #append users only from row greater than offset
                    #obtained csv file name from csv_list using index
                    _csv = csv_list[active_client - 1] 
                    #print(csv_file_index)
                    if line_index > int(offset_dicts[_csv]) :
                        client(InviteToChannelRequest(target_group_entity, [user_to_add]))
                    else :
                        continue    
                else :
                    
                    _csv = csv_list[active_client - 1] 
                    client(InviteToChannelRequest(target_group_entity, [user_to_add]))
                    if grp_not_found :
                        #then we just replace only for the group
                        data_list[_csv] = line_index
                        
                    else :
                        #then we assume  case for missing file
                        new_offset_data = {}  #offset data for a file
                        new_offset_data[_csv] = line_index
                        new_data_list.append(new_offset_data)
                        
            
            #time.sleep(1)
            global Users_Added 
            global add_no
            Users_Added += 1
            current_add += 1
            line_index += 1
            if Users_Added == add_no : 
                print("Added {} members,exiting ..".format(Users_Added))
                break
        except PeerFloodError:
            print("Getting Flood Error from telegram. Script is stopping now. Please try again after some time.")
            time.sleep(10)
            continue
        except UserPrivacyRestrictedError:
            print("The user's privacy settings do not allow you to do this. Skipping.")
            #time.sleep(5)
            #input()
            continue
        except:
            traceback.print_exc()
            print("Unexpected Error")
            #time.sleep(5)
            #input()
            continue
 
    print("Added {} members in this iteration,total {}".format(current_add,Users_Added))
    if offset_data : 
        json_data[target_group.title] = data_list
    json_data[target_group.title] = new_data_list
    #update offset file to new csv line indexes
    with open(offset_file,'w') as jf :
        json.dump(json_data,jf)
    return 





def main() :
    global Users_Added
    Users_Added = 0
    link = 't.me/joinchat/RyHbZrUzf-1YMMtE'
    global add_no
    add_no = input("How many users do you want to add  : ")
    add_no = int(add_no)
    clients,nature = get_clients(add_no)
    if not clients : print("The entered username does not exist,please crosscheck")
    if nature == "single" :
        pass

    elif nature == "multiple" :
        #uses one instance of client to get group
        group = get_group(clients[0])
        #reset_offset = input("Do you want to rese")
        users_list   =  get_users(csv_list,add_no)
        global active_client
        active_client = 0
        skip_offset,grp_not_found,data_list = get_offset_data(offset_file='offset_file.json',group_title=group.title)
        for client,users in zip(clients,users_list) :
            active_client += 1
            add_users(client,
             users,
              group,
              csv_list,
              skip_offset,
              grp_not_found,
              data_list)    
            input()



if __name__ == "__main__" : main()