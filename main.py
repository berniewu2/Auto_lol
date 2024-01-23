import time
import sys
import json
import os, os.path
import urllib3
from lcu_driver import Connector
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter.font import Font
from threading import Thread


client = Connector()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
global am_i_assigned, am_i_picking, am_i_banning, ban_number, phase, picks, bans, in_game, summoner_name, accept, ban, select, first_lane, second_lane
am_i_assigned = False
am_i_banning = False
am_i_picking = False
in_game = False
phase = ''
picks = []
bans = []
pick_number = 0
ban_number = 0


@client.ready
async def lcu_ready(connection):
    global summoner_id, champions_map, summoner_name
    temp_champions_map = {}
    summoner = await connection.request("get",'/lol-summoner/v1/current-summoner')
    summoner_to_json = await summoner.json()
    summoner_name = summoner_to_json['gameName']
    print(f'Log in as: {summoner_name}')
    messagebox.showinfo("Login", f'Log in as: {summoner_name}')
    summoner_id = summoner_to_json['summonerId']
    
    champion_list = await connection.request('get', f'/lol-champions/v1/inventories/{summoner_id}/champions-minimal')
    champion_list_to_json = await champion_list.json()
    for i in range(len(champion_list_to_json)):
        temp_champions_map.update({champion_list_to_json[i]['name']: champion_list_to_json[i]['id']})
    champions_map = temp_champions_map



@client.ws.register('/lol-matchmaking/v1/ready-check',event_types=("UPDATE",))
async def auto_accept_match(connection,event):
    if event.data['playerResponse'] == "None" and accept:
        await connection.request('post','/lol-matchmaking/v1/ready-check/accept')
        print("Match has been accepted")

@client.ws.register('/lol-champ-select/v1/session', event_types=('CREATE', 'UPDATE',))
async def champ_select_changed(connection, event):
    global am_i_assigned, pick_number, ban_number, am_i_banning, am_i_picking, phase, bans, picks, have_i_prepicked, in_game, action_id, first_lane, second_lane
    have_i_prepicked = False
    lobby_phase = event.data['timer']['phase']
    local_player_cell_id = event.data['localPlayerCellId']
    for teammate in event.data['myTeam']:
        if teammate['cellId'] == local_player_cell_id:
            assigned_position = teammate['assignedPosition']
            if assigned_position == 'middle': assigned_position = '3'
            elif assigned_position == 'jungle': assigned_position = '2'
            elif assigned_position == 'top': assigned_position = '1'
            elif assigned_position == 'bottom': assigned_position = '4'
            elif assigned_position == 'utility': assigned_position = '5'
            am_i_assigned = True

    for action in event.data['actions']:
        for actionArr in action:
            if actionArr['actorCellId'] == local_player_cell_id and actionArr['isInProgress'] == True:
                phase = actionArr['type']
                action_id = actionArr['id']
                if phase == 'ban':
                    am_i_banning = actionArr['isInProgress']
                if phase == 'pick':
                    am_i_picking = actionArr['isInProgress']

    if phase == 'ban' and lobby_phase == 'BAN_PICK' and am_i_banning and ban:
        while am_i_banning:
            try:
                if assigned_position == first_lane[0]:
                    ban_champ = first_lane[2]
                    for teammate in event.data['myTeam']:
                        if teammate['championPickIntent'] == champions_map[ban_champ]:
                            ban_champ = first_lane[3]
                    for teammate in event.data['myTeam']:
                        if teammate['championPickIntent'] == champions_map[ban_champ]:
                            ban_champ = 'None'
                else:
                    ban_champ = second_lane[2]
                    for teammate in event.data['myTeam']:
                        if teammate['championPickIntent'] == champions_map[ban_champ]:
                            ban_champ = second_lane[3]
                    for teammate in event.data['myTeam']:
                        if teammate['championPickIntent'] == champions_map[ban_champ]:
                            ban_champ = 'None'
                
                await connection.request('patch', '/lol-champ-select/v1/session/actions/%d' % action_id,
                                         data={"championId": champions_map[ban_champ], "completed": True})
                am_i_banning = False
            except (Exception,):
                pass
    if phase == 'pick' and lobby_phase == 'BAN_PICK' and am_i_picking and select:
        while am_i_picking:
            try:
                if assigned_position == first_lane[0]:
                    select_champ = first_lane[1]
                else:
                    select_champ = second_lane[1]
                await connection.request('patch', '/lol-champ-select/v1/session/actions/%d' % action_id,
                                         data={"championId": champions_map[select_champ], "completed": True})
                am_i_picking = False
            except (Exception,):
                pass
    if lobby_phase == 'PLANNING' and not have_i_prepicked:
        try:
            await connection.request('patch', '/lol-champ-select/v1/session/actions/%d' % action_id,
                                     data={"championId": champions_map[select_champ], "completed": False})
            have_i_prepicked = True
        except (Exception,):
            print(Exception)
    if lobby_phase == 'FINALIZATION':
        time.sleep(2)

@client.close
async def disconnect(_):
    print('The client has been closed!')
    raise SystemExit

champ_list = ['Aatrox', 'Ahri', 'Akali', 'Akshan', 'Alistar', 'Amumu', 'Anivia', 'Annie', 'Aphelios', 'Ashe', 'Aurelion Sol', 'Azir', 'Bard', "Bel'Veth", 'Blitzcrank', 'Brand', 'Braum', 'Briar', 'Caitlyn', 'Camille', 'Cassiopeia', "Cho'Gath", 'Corki', 'Darius', 'Diana', 'Dr. Mundo', 'Draven', 'Ekko', 'Elise', 'Evelynn', 'Ezreal', 'Fiddlesticks', 'Fiora', 'Fizz', 'Galio', 'Gangplank', 'Garen', 'Gnar', 'Gragas', 'Graves', 'Gwen', 'Hecarim', 'Heimerdinger', 'Hwei', 'Illaoi', 'Irelia', 'Ivern', 'Janna', 'Jarvan IV', 'Jax', 'Jayce', 'Jhin', 'Jinx', "K'Sante", "Kai'Sa", 'Kalista', 'Karma', 'Karthus', 'Kassadin', 'Katarina', 'Kayle', 'Kayn', 'Kennen', "Kha'Zix", 'Kindred', 'Kled', "Kog'Maw", 'LeBlanc', 'Lee Sin', 'Leona', 'Lillia', 'Lissandra', 'Lucian', 'Lulu', 'Lux', 'Malphite', 'Malzahar', 'Maokai', 'Master Yi', 'Milio', 'Miss Fortune', 'Mordekaiser', 'Morgana', 'Naafiri', 'Nami', 'Nasus', 'Nautilus', 'Neeko', 'Nidalee', 'Nilah', 'Nocturne', 'None', 'Nunu & Willump', 'Olaf', 'Orianna', 'Ornn', 'Pantheon', 'Poppy', 'Pyke', 'Qiyana', 'Quinn', 'Rakan', 'Rammus', "Rek'Sai", 'Rell', 'Renata Glasc', 'Renekton', 'Rengar', 'Riven', 'Rumble', 'Ryze', 'Samira', 'Sejuani', 'Senna', 'Seraphine', 'Sett', 'Shaco', 'Shen', 'Shyvana', 'Singed', 'Sion', 'Sivir', 'Skarner', 'Sona', 'Soraka', 'Swain', 'Sylas', 'Syndra', 'Tahm Kench', 'Taliyah', 'Talon', 'Taric', 'Teemo', 'Thresh', 'Tristana', 'Trundle', 'Tryndamere', 'Twisted Fate', 'Twitch', 'Udyr', 'Urgot', 'Varus', 'Vayne', 'Veigar', "Vel'Koz", 'Vex', 'Vi', 'Viego', 'Viktor', 'Vladimir', 'Volibear', 'Warwick', 'Wukong', 'Xayah', 'Xerath', 'Xin Zhao', 'Yasuo', 'Yone', 'Yorick', 'Yuumi', 'Zac', 'Zed', 'Zeri', 'Ziggs', 'Zilean', 'Zoe', 'Zyra']


def check_input(event):
    value = event.widget.get()

    if value == '':
        event.widget['values'] = champ_list
    else:
        data = [item for item in champ_list if value.lower() in item.lower()]
        event.widget['values'] = data

def begin():
    client.start()

def threading(): 
    if not t1.is_alive():    
        t1.start()
    get_values()

def get_values():
   
    check_values = {
        'accept': chk_var1.get(),
        'ban': chk_var2.get(),
        'select': chk_var3.get()
    }
    global accept, ban, select, first_lane, second_lane
    accept = chk_var1.get()
    ban = chk_var2.get()
    select = chk_var3.get()

    radio_value_first = first_lane_choice.get()
    combo_value_first = first_select.get()

    first_lane_values = {
        'select': combo_value_first,
        'Ban_1': first_ban_1.get(),
        'Ban_2': first_ban_2.get()
    }
    
    first_lane = [radio_value_first, combo_value_first, first_ban_1.get(), first_ban_2.get()]
    
    radio_value_second = second_lane_choice.get()
    combo_value_second = second_select.get()

    second_lane_values = {
        'select': combo_value_second,
        'Ban_1': second_ban_1.get(),
        'Ban_2': second_ban_2.get()
    }
    second_lane = [radio_value_second, combo_value_second, second_ban_1.get(), second_ban_2.get()]

    all_values = {
        'choices': check_values,
        'first_lane': {
            'lane': radio_value_first,
            'champ': first_lane_values
        },
        'second_lane': {
            'lane': radio_value_second,
            'champ': second_lane_values
        }
    }

    return(all_values)
import asyncio

async def end():
    await client.stop()

def on_closing():
    window.destroy()
    sys.exit()
    asyncio.run(end())




window = Tk()
window.geometry('550x500')
window.title('Auto lol')
text_font = Font(family="Helvetica", size=16)
# Creating Checkboxes
chk_var1 = IntVar(value=1)
chk_var2 = IntVar()
chk_var3 = IntVar()

chk1 = Checkbutton(window, text='Auto accept', variable=chk_var1, font=text_font)
chk2 = Checkbutton(window, text='Auto ban', variable=chk_var2, font=text_font)
chk3 = Checkbutton(window, text='Auto pick', variable=chk_var3, font=text_font)


values = {"top" : "1", 
        "jungle" : "2", 
        "mid" : "3", 
        "adc" : "4", 
        "support" : "5"} 
current_y = 10

chk1.place(x= 10, y= current_y)
chk2.place(x= 170, y= current_y)
chk3.place(x= 310, y= current_y)

current_y += 40

Label(window, text="First lane", font=Font(family="Helvetica", size=18)).place(x=10, y=current_y)
current_y += 40

first_lane_choice = StringVar(window, "1") 
for (text, value) in values.items(): 
    Radiobutton(window, text = text, variable = first_lane_choice, 
        value = value, font=text_font).place(x=90*(int(value)-1)+10,y=current_y) 
current_y += 50

Label(window, text="Champion", font=text_font).place(x=10, y=current_y)

first_select = ttk.Combobox(window)
first_select['values'] = champ_list
first_select.bind('<KeyRelease>', check_input)
first_select.place(x=150, y= current_y + 5)
current_y += 30

Label(window, text="Ban 1", font=text_font).place(x=10, y=current_y)
first_ban_1 =ttk.Combobox(window)
first_ban_1['values'] = champ_list
first_ban_1.bind('<KeyRelease>', check_input)
first_ban_1.place(x=100, y= current_y + 5)
current_y += 30

Label(window, text="Ban 2", font=text_font).place(x=10, y=current_y)
first_ban_2 =ttk.Combobox(window)
first_ban_2['values'] = champ_list
first_ban_2.bind('<KeyRelease>', check_input)
first_ban_2.place(x=100, y= current_y + 5)
current_y += 50

Label(window, text="Second lane", font=Font(family="Helvetica", size=18)).place(x=10, y=current_y)
current_y += 40

second_lane_choice = StringVar(window, "2") 
for (text, value) in values.items(): 
    Radiobutton(window, text = text, variable = second_lane_choice, 
        value = value, font=text_font).place(x=90*(int(value)-1)+10,y=current_y) 
current_y += 50

Label(window, text="Champion", font=text_font).place(x=10, y=current_y)
second_select =ttk.Combobox(window)
second_select['values'] = champ_list
second_select.bind('<KeyRelease>', check_input)
second_select.place(x=150, y= current_y + 5)

current_y += 30

Label(window, text="Ban 1", font=text_font).place(x=10, y=current_y)
second_ban_1 =ttk.Combobox(window)
second_ban_1['values'] = champ_list
second_ban_1.bind('<KeyRelease>', check_input)
second_ban_1.place(x=100, y= current_y + 5)
current_y += 30
Label(window, text="Ban 2", font=text_font).place(x=10, y=current_y)
second_ban_2 =ttk.Combobox(window)
second_ban_2['values'] = champ_list
second_ban_2.bind('<KeyRelease>', check_input)
second_ban_2.place(x=100, y= current_y + 5)

ok_button = Button(window, text='OK', command=threading, width= 40, borderwidth=5)
ok_button.place(x=10, y=450)


def load():
    if os.path.isfile('profile.json'):
        with open('profile.json', 'r') as file:
            data = json.load(file)
            if data['choices']['accept'] : chk1.select()
            if data['choices']['ban'] : chk2.select()
            if data['choices']['select'] : chk3.select()
            first_lane_choice.set(data['first_lane']['lane'])
            second_lane_choice.set(data['second_lane']['lane'])
            first_select.current(champ_list.index(data['first_lane']['champ']['select']))
            first_ban_1.current(champ_list.index(data['first_lane']['champ']['Ban_1']))
            first_ban_2.current(champ_list.index(data['first_lane']['champ']['Ban_2']))
            second_select.current(champ_list.index(data['second_lane']['champ']['select']))
            second_ban_1.current(champ_list.index(data['second_lane']['champ']['Ban_1']))
            second_ban_2.current(champ_list.index(data['second_lane']['champ']['Ban_2']))


def save():
    with open('profile.json', 'w+') as file:
        file.write(json.dumps(get_values()))
    
Button(window, text="save", command=save, borderwidth=5, width= 8).place(x=320, y=450)
Button(window, text="load", command=load, borderwidth=5, width= 8).place(x=400, y=450)
Button(window, text="Quit", command=window.destroy, borderwidth=5).place(x=490, y=450)
window.protocol("WM_DELETE_WINDOW", on_closing)


if __name__ == '__main__':
    t1=Thread(target=begin)
    t1.daemon = True
    window.mainloop()