ScriptName = "PB"
Website = "https://speedrun.com/"
Description = "Pulls Personal Best for a Category when called with 'commandName Category'" #See Line 15
Creator = "AuroTheAzure"
Version = "1.1.1"

''' 
Notes:
    Cooldowns on lines 16 and 17 are in seconds.
    Line 16 is the command cooldown
    Line 17 is the individual user cooldown
    Match Category in Twitch Title to the Tab in hte main board. :) (Any% | World Peace | All Red Berries | 70 Star etc.
'''

commandName = "!pb"     #String to start the command
cooldown = 1            #Cooldown of the command in seconds
userCooldown = 1        #Cooldown for individual user
runner_name = 'Auro'

import datetime         #For converting time from a number of seconds to a human readable format (1:23:45.67)
import json             #For quickly / easily parsing data from speedrun.com/


headers = {'Client-ID': 'umyyc7qkoxedtjir8wo50iinz6qzs8'}  #No touchey

def Init():
    return


def Execute(data):
    if data.GetParam(0) != commandName or Parent.IsOnCooldown(ScriptName, commandName) or not Parent.IsLive() or Parent.IsOnUserCooldown(ScriptName, commandName, data.User):
        #If we're not called with our command name, or we're on cooldown, or the user who called it is on cooldown, quit.
        #Parent.Log("!pb", "The game is {}".format(game))
        return
    else:
        game, title = getGame()
        if game == -1 and title == -1:
            send_message("There was an issue grabbing the game / title from Twitch.")
            return
        gameURL = SpeedrunGame(game)
        id, category = getCategories(gameURL, title)
        #Parent.Log("!pb", "{} {}".format(id, category))
        if id == -5 and category == -5:            # This means the category wasn't found in the twitch title
            send_message("I couldn't find any categories in the stream title.")
            Parent.AddUserCooldown(ScriptName, commandName, data.User, userCooldown)
            Parent.AddCooldown(ScriptName, commandName, cooldown)
            return
        elif id == -2 and category == -2:          # This means the category page failed to load.
            send_message("Contact the creator, because your game is not currently supported.") #Gotta get more work somehow :)
            Parent.AddUserCooldown(ScriptName, commandName, data.User, userCooldown)
            Parent.AddCooldown(ScriptName, commandName, cooldown)
            return
        run = getPB(id)
        if run == -3:
            send_message("{} has no verified PB in {} {}.".format(runner_name, game, category))
            Parent.AddUserCooldown(ScriptName, commandName, data.User, userCooldown)
            Parent.AddCooldown(ScriptName, commandName, cooldown)
            return
        #Parent.Log("!pb", str(run))
        Time = run['times']['primary_t']
        #Parent.Log("!pb", str(type(Time)))
        TimeParsed = datetime.timedelta(seconds=Time)
        TimeString = str(TimeParsed)
        while TimeString[0] == '0' or TimeString[0] == ':':
            TimeString = TimeString[1::]
        if '.' in TimeString:
            TimeString = TimeString[0:TimeString.index('.')+4] # Cut the time down to 3 decimal places at most

        send_message("{}'s PB in {} {} is {}.".format(runner_name, game, category, TimeString))
        Parent.AddUserCooldown(ScriptName, commandName, data.User, userCooldown)
        Parent.AddCooldown(ScriptName, commandName, cooldown)
	return


def Tick():
    return


def SpeedrunGame(TwitchGameName):
    #TwitchGameName is Game according to Twitch
    #Format for the return is [mainboard, category extension]
    if TwitchGameName == "Super Mario Odyssey":     #SMO Main board
        return ["smo", "smoce"]
    elif TwitchGameName == "Super Mario 64":        #SM64 Main Board
        return ["sm64", "sm64memes"]
    elif TwitchGameName == "Celeste":               #Celeste Main Board
        return ["celeste", "celeste_category_extensions"]
    elif TwitchGameName == "Super Mario Sunshine":
        return ["sms", "smsce"]
    elif TwitchGameName == "The Legend of Zelda: Breath of the Wild":
        return ["botw", "botw-extension"]
    elif TwitchGameName == "Super Mario Bros.":
        return ["smb1", "smbce"]
    elif TwitchGameName == "Super Mario Bros.: The Lost Levels":
        return ["smbtll", "smbtllce"]
    elif TwitchGameName == "Super Mario Bros. 2":
        return ["smb2", "smb2ce"]
    elif TwitchGameName == "Super Mario Bros. 3":
        return ["smb3", "smb3ce"]
    elif TwitchGameName == "Super Mario World":
        return ["smw", "smwext"]
    elif TwitchGameName == "Super Mario Galaxy":
        return ["smg1", "smgce"]
    elif TwitchGameName == "Super Mario Galaxy 2":
        return ["smg2", "smg2"]
    elif TwitchGameName == "New Super Mario Bros.":
        return ["nsmb", "nsmbce"]
    elif TwitchGameName == "New Super Mario Bros. 2":
        return ["nsmb2", "nsmb2memes"]
    elif TwitchGameName == "New Super Mario Bros. U":
        return ["nsmbu", "nsmbu"]
    elif TwitchGameName == "New Super Mario Bros. Wii":
        return ["nsmbw", "nsmbwce"]
    elif TwitchGameName == "Super Mario 3D World":
        return ["sm3dw", "sm3dw"]
    elif TwitchGameName == "Yu-Gi-Oh! Forbidden Memories":
        return ["yugiohfm", "yugiohfmextensions"]
        

def getRunnerName(speedrunner_id):
    #Get the runners ID from speedrun.com to query the speedrun API less.
    #Parent.Log("!pb", "Pulling from speedrun.com/api/v1/users/{}".format(speedrunner_id))
    runnerPage = Parent.GetRequest("https://speedrun.com/api/v1/users/{}".format(speedrunner_id), {})
    runnerPage = json.loads(runnerPage)                     #Get speedrun.com data for user code
    #Parent.Log("!pb", "Runner Page: {}".format(runnerPage))
    runnerPage = json.loads(runnerPage['response'])
    speedrunner_name = runnerPage['data']['names']['international']   #Grab international name for runner
    #Parent.Log("!pb", "Runner Name is {}".format(speedrunner_name))
    return speedrunner_name
	
    
def getGame():
    # Pulls the json blob from Decapi.me, and returns the Game (As a string), and the Title of the stream.
    # Parent.Log("!wr", "Pulling stream information from decapi.me")
    GameName = Parent.GetRequest("https://decapi.me/twitch/game/{}".format(Parent.GetChannelName()), headers)
    GameName = json.loads(GameName) # Parent.GetRequest pulls information back as a string, we're converting it to a json object
    if GameName['status'] == 200:  # If successful response
        game = GameName['response']
        title = Parent.GetRequest("https://decapi.me/twitch/title/{}".format(Parent.GetChannelName()), headers)
        title = json.loads(title)
        if title['status'] == 200:
            title = title['response']
            # Parent.Log("!wr", "Title is {}".format(title))
            # Parent.Log("!wr", "Game is {}".format(game))
            return game, title
        else:
            return -5, -5
    return -1, -1


def getCategories(game, TwitchTitle):
    #Uses the speedrun API to get a list of category names for the game being run
    #This functions returns a link to the leaderboard page, and the name of the category to print later...
    #Debating returning the blob
    categories = {}     # Category : Records Page
    #Parent.Log("!pb", "Getting list of category names from speedrun.com.")
    '''
    if "IL" in title:
        TYPE = 'per-level'
    else:
        TYPE = 'per-game'
    '''
    for each in game:
        CategoryPage = Parent.GetRequest("https://speedrun.com/api/v1/games/{}/categories".format(each), {})
        CategoryPage = json.loads(CategoryPage)
        if CategoryPage['status'] == 200:
            CategoryPage = json.loads(CategoryPage['response'])
            TwitchTitleUpper = TwitchTitle.upper()
            for each in CategoryPage['data']:
                #Parent.Log("!pb", "checking for {} in Title.".format(each['name']))
                if each['name'].upper() in TwitchTitleUpper and each['type'] == "per-game":
                    categories[each['name']] = each['id']
        else:   #Failed to load the categories page for the game ('game' value does not point to a valid page)
            Parent.Log("!pb", "{} has no categories page.".format(each))
            return -2, -2
    if categories:
        LongestMatch = max(categories.keys(),key=len)
        return categories[LongestMatch], LongestMatch
    else:   
        #If we found no matching category in the title of the stream
        Parent.Log("!pb", "Error pulling the categories for {}.".format(game))
        return -5, -5
    
def getPB(id):
    #Pull the list of runs from the speedrun api
    RunnerPBs = Parent.GetRequest("https://www.speedrun.com/api/v1/users/{}/personal-bests".format(runner_name), {})
    RunnerPBs = json.loads(RunnerPBs)
    #Parent.Log("!pb", str(RunnerPBs))
    #Parent.Log("!pb", "Category id is {}".format(id))
    if RunnerPBs['status'] != 200:
        Parent.Log("There was an issue getting {}s Personal Bests".format(runner_name))
        return "Blame speedrun.com for being broken. :)"
    PBs = json.loads(RunnerPBs['response'])
    for each in PBs['data']:
        #Parent.Log("!pb", str(each))
        if each['run']['category'] == id:
            return each['run']
    return -3

def send_message(message):
    Parent.SendStreamMessage(message)
    return
