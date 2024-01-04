import time
import urllib3
from lcu_driver import Connector
import PySimpleGUI as psg


client = Connector()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
global am_i_assigned, am_i_picking, am_i_banning, ban_number, phase, picks, bans, in_game, summoner_name, accept, ban, select
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
    global am_i_assigned, pick_number, ban_number, am_i_banning, am_i_picking, phase, bans, picks, have_i_prepicked, in_game, action_id
    have_i_prepicked = False
    lobby_phase = event.data['timer']['phase']
    local_player_cell_id = event.data['localPlayerCellId']
    for teammate in event.data['myTeam']:
        if teammate['cellId'] == local_player_cell_id:
            assigned_position = teammate['assignedPosition']
            if assigned_position == 'middle': assigned_position = 'mid'
            elif assigned_position == 'jungle': assigned_position = 'jg'
            elif assigned_position == 'top': assigned_position = 'top'
            elif assigned_position == 'bottom': assigned_position = 'adc'
            elif assigned_position == 'utility': assigned_position = 'sup'
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
                    ban_champ = first_lane[1]
                else:
                    ban_champ = second_lane[1]
                await connection.request('patch', '/lol-champ-select/v1/session/actions/%d' % action_id,
                                         data={"championId": champions_map[ban_champ], "completed": True})
                # ban_number += 1
                am_i_banning = False
            except (Exception,):
                # ban_number += 1
                # if ban_number > len(
                #         bans):  # Due to some lcu bugs I have to do this to correct a bug that may happen in draft custom
                #     ban_number = 0
                pass
    if phase == 'pick' and lobby_phase == 'BAN_PICK' and am_i_picking and select:
        while am_i_picking:
            try:
                if assigned_position == first_lane[0]:
                    select_champ = first_lane[2]
                else:
                    select_champ = second_lane[2]
                await connection.request('patch', '/lol-champ-select/v1/session/actions/%d' % action_id,
                                         data={"championId": champions_map[select_champ], "completed": True})
                am_i_picking = False
            except (Exception,):

                pass
    if lobby_phase == 'PLANNING' and not have_i_prepicked:
        try:
            await connection.request('patch', '/lol-champ-select/v1/session/actions/%d' % action_id,
                                     data={"championId": champions_map['Trundle'], "completed": False})
            have_i_prepicked = True
        except (Exception,):
            print(Exception)
    if lobby_phase == 'FINALIZATION':
        time.sleep(2)
@client.close
async def disconnect(_):
    print('The client has been closed!')
    await client.stop()
    

print("""    /\        | |        | |     | |
   /  \  _   _| |_ ___   | | ___ | |
  / /\ \| | | | __/ _ \  | |/ _ \| |
 / ____ \ |_| | || (_) | | | (_) | |
/_/    \_\__,_|\__\___/  |_|\___/|_|
                                        
""")

print("\nClose this window will stop the application\n")
psg.set_options(font=("Arial Bold",14))
title=psg.Text(f"Auto League", text_color= 'gold2')
choices=[]
finished = False
choices.append(psg.Checkbox("Auto Accept", key='accept', default= True))
choices.append(psg.Checkbox("Auto Ban", key='ban', default= True))
choices.append(psg.Checkbox("Auto Select", key='select', default= True))

champ_list = ['Aatrox', 'Ahri', 'Akali', 'Akshan', 'Alistar', 'Amumu', 'Anivia', 'Annie', 'Aphelios', 'Ashe', 'Aurelion Sol', 'Azir', 'Bard', "Bel'Veth", 'Blitzcrank', 'Brand', 'Braum', 'Briar', 'Caitlyn', 'Camille', 'Cassiopeia', "Cho'Gath", 'Corki', 'Darius', 'Diana', 'Dr. Mundo', 'Draven', 'Ekko', 'Elise', 'Evelynn', 'Ezreal', 'Fiddlesticks', 'Fiora', 'Fizz', 'Galio', 'Gangplank', 'Garen', 'Gnar', 'Gragas', 'Graves', 'Gwen', 'Hecarim', 'Heimerdinger', 'Hwei', 'Illaoi', 'Irelia', 'Ivern', 'Janna', 'Jarvan IV', 'Jax', 'Jayce', 'Jhin', 'Jinx', "K'Sante", "Kai'Sa", 'Kalista', 'Karma', 'Karthus', 'Kassadin', 'Katarina', 'Kayle', 'Kayn', 'Kennen', "Kha'Zix", 'Kindred', 'Kled', "Kog'Maw", 'LeBlanc', 'Lee Sin', 'Leona', 'Lillia', 'Lissandra', 'Lucian', 'Lulu', 'Lux', 'Malphite', 'Malzahar', 'Maokai', 'Master Yi', 'Milio', 'Miss Fortune', 'Mordekaiser', 'Morgana', 'Naafiri', 'Nami', 'Nasus', 'Nautilus', 'Neeko', 'Nidalee', 'Nilah', 'Nocturne', 'None', 'Nunu & Willump', 'Olaf', 'Orianna', 'Ornn', 'Pantheon', 'Poppy', 'Pyke', 'Qiyana', 'Quinn', 'Rakan', 'Rammus', "Rek'Sai", 'Rell', 'Renata Glasc', 'Renekton', 'Rengar', 'Riven', 'Rumble', 'Ryze', 'Samira', 'Sejuani', 'Senna', 'Seraphine', 'Sett', 'Shaco', 'Shen', 'Shyvana', 'Singed', 'Sion', 'Sivir', 'Skarner', 'Sona', 'Soraka', 'Swain', 'Sylas', 'Syndra', 'Tahm Kench', 'Taliyah', 'Talon', 'Taric', 'Teemo', 'Thresh', 'Tristana', 'Trundle', 'Tryndamere', 'Twisted Fate', 'Twitch', 'Udyr', 'Urgot', 'Varus', 'Vayne', 'Veigar', "Vel'Koz", 'Vex', 'Vi', 'Viego', 'Viktor', 'Vladimir', 'Volibear', 'Warwick', 'Wukong', 'Xayah', 'Xerath', 'Xin Zhao', 'Yasuo', 'Yone', 'Yorick', 'Yuumi', 'Zac', 'Zed', 'Zeri', 'Ziggs', 'Zilean', 'Zoe', 'Zyra']

lane_text_1=psg.Text(f"First lane")
lane_1=[]
lane_1.append(psg.Radio("top", "lane_1", key='top_1', enable_events=True,default=True))
lane_1.append(psg.Radio("jungle", "lane_1", key='jungle_1', enable_events=True))
lane_1.append(psg.Radio("mid", "lane_1", key='mid_1',enable_events=True))
lane_1.append(psg.Radio("adc", "lane_1", key='adc_1', enable_events=True))
lane_1.append(psg.Radio("support", "lane_1", key='sup_1',enable_events=True))
champ_1=psg.Text("Champ")
champ_dd_1 = psg.DD(champ_list, size=(10,8),enable_events=True, key='select_1')
ban_1=psg.Text("Ban", text_color='VioletRed3')
b1 = psg.DD(champ_list, size=(10,8),enable_events=True, key='ban_1')

lane_text_2=psg.Text(f"Second lane")
lane_2=[]
lane_2.append(psg.Radio("top", "lane_2", key='top_2', enable_events=True))
lane_2.append(psg.Radio("jungle", "lane_2", key='jungle_2', enable_events=True,default=True))
lane_2.append(psg.Radio("mid", "lane_2", key='mid_2',enable_events=True))
lane_2.append(psg.Radio("adc", "lane_2", key='adc_2', enable_events=True))
lane_2.append(psg.Radio("support", "lane_2", key='sup_2',enable_events=True))
champ_2=psg.Text("Champ")
champ_dd_2= psg.DD(champ_list, size=(10,8),enable_events=True, key='select_2')
ban_2=psg.Text("Ban", text_color='VioletRed3')
b2 = psg.DD(champ_list, size=(10,8),enable_events=True, key='ban_2')

ok=psg.Button("OK")
exit=psg.Button("Exit")
layout=[[title],[choices],[lane_text_1],[lane_1],[champ_1,champ_dd_1],[ban_1,b1],[lane_text_2],[lane_2],[champ_2,champ_dd_2],[ban_2,b2],[ok, exit]]

window = psg.Window('百鬼あやめ', layout, size=(700,450))
while True:
    event, values = window.read()
    # print (event, values)
    if event in (psg.WIN_CLOSED, 'Exit'): 
        finished = True
        break
    window['select_1'].update(visible = values['select'])
    window['ban_1'].update(visible = values['ban'])
    window['select_2'].update(visible = values['select'])
    window['ban_2'].update(visible = values['ban'])

    if event=='OK':
        result = values
        break


window.close()
if not finished:
    accept = result['accept']
    ban = result['ban']
    select = result['select']
    if result['top_1']:
        first_lane = ['top']
    elif result['jungle_1']:
        first_lane = ['jg']
    elif result['mid_1']:
        first_lane = ['mid']
    elif result['adc_1']:
        first_lane = ['adc']
    elif result['sup_1']:
        first_lane = ['sup']

    if result['top_2']:
        second_lane = ['top']
    elif result['jungle_2']:
        second_lane = ['jg']
    elif result['mid_2']:
        second_lane = ['mid']
    elif result['adc_2']:
        second_lane = ['adc']
    elif result['sup_2']:
        second_lane = ['sup']
    first_lane.append(result['ban_1'])
    first_lane.append(result['select_1'])

    second_lane.append(result['ban_2'])
    second_lane.append(result['select_2'])


    print(f'first choice: {first_lane}')
    print(f'second choice: {second_lane}\n')
    client.start()