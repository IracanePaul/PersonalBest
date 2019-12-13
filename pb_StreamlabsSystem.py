ScriptName = "PB"
Website = "https://speedrun.com/"
Description = "Pulls Personal Best for a Category when called with 'commandName Category'" #See Line 15
Creator = "AuroTheAzure"
Version = "1.1.0"

''' 
Notes:
    Currently only works with top 50 runners.  For some weird reason code can't pull back past runner...58 or so, so 50 to be safe.
    Please make sure the name on like 18 matches your speedrun.com username
    Cooldown on line 16 is in seconds.
    Match Category in Twitch Title to the Tab in hte main board. :) (Any% | World Peace | All Red Berries | 70 Star etc.
'''

commandName = "!pb"     #String to start the command
cooldown = 1            #Cooldown of the command in seconds
runner_name = "EnsgMaster"        #Runner name as it appears on speedrun.com/

import datetime         #For converting time from a number of seconds to a human readable format (1:23:45.67)
import json             #For quickly / easily parsing data from speedrun.com/


headers = {'Client-ID': 'umyyc7qkoxedtjir8wo50iinz6qzs8'}  #No touchey

def Init():
    return


def Execute(data):
    if data.GetParam(0) != commandName or Parent.IsOnCooldown(ScriptName, commandName) or not Parent.IsLive():
        #If we're not called with our command name, or we're on cooldown, quit.
        #Parent.Log("!pb", "The game is {}".format(game))
        return
    else:
        game, title = getGame()
        if game == -1 and title == -1:
            send_message("There was an issue grabbing the game / title from Twitch.")
            return
        gameURL = SpeedrunGame(game)
        url, category = getCategories(gameURL, title)
        Parent.Log("!pb", "url is {}; category is {}".format(url, category))
        if url == -5 and category == -5:            # This means the category wasn't found in the twitch title
            gameURL = CategoryExtensions(game)
            url, category = getCategories(gameURL, title)
            Parent.Log("!pb", "url is {}; category is {}".format(url, category))
        elif url == -2 and category == -2:          # This means the category page failed to load.
            send_message("Contact the creator, because your game is not currently supported.") #Gotta get more work somehow :)
            return
        runs = getRuns(url)
        runnerID = getRunnerId(runner_name)
        
        pbrun = {}
        for run in runs:
            #Parent.Log("!pb", str(run))
            id = run['run']['players'][0]['id']
            if id == runnerID:
                pbrun = run
                Parent.Log("!pb", str(pbrun))
                break
        Time = pbrun['run']['times']['primary_t']
        TimeParsed = datetime.timedelta(seconds=Time)
        TimeString = str(TimeParsed)
        while TimeString[0] == '0' or TimeString[0] == ':':
            TimeString = TimeString[1::]
        send_message("{} PB in {} {} is {}".format(runner_name, game, category, TimeString))
	return


def Tick():
    return


def SpeedrunGame(TwitchGameName):
    #TwitchGameName is Game according to Twitch
    if TwitchGameName == "Super Mario Odyssey":     #SMO Main board
        return "smo"
    elif TwitchGameName == "Super Mario 64":        #SM64 Main Board
        return "sm64"
    elif TwitchGameName == "Celeste":               #Celeste Main Board
        return "celeste"
    elif TwitchGameName == "Super Mario Sunshine":
        return "sms"
    elif TwitchGameName == "Yu-Gi-Oh! Forbidden Memories":
        return "yugiohfm"

def CategoryExtensions(TwitchGameName):
    #TwitchGameName is the Game according to Twitch
    if TwitchGameName == "Super Mario Odyssey":     #SMO Category Extensions
        return "smoce"
    elif TwitchGameName == "Super Mario 64":        #SM64 Category Extensions
        return "sm64memes"
    elif TwitchGameName == "Celeste":               #Celeste Category Extensions
        return "celeste_category_extensions"
    elif TwitchGameName == "Super Mario Sunshine":
        return "smsce"
    elif TwitchGameName == "Yu-Gi-Oh! Forbidden Memories":
        return "yugiohfmextensions"

def getRunnerId(speedrunner_name):
    #Get the runners ID from speedrun.com to query the speedrun API less.
    Parent.Log("!pb", "Pulling from speedrun.com/api/v1/users/{}".format(speedrunner_name))
    runnerPage = Parent.GetRequest("https://speedrun.com/api/v1/users/{}".format(speedrunner_name), {})
    runnerPage = json.loads(runnerPage)                     #Get speedrun.com data for user code
    Parent.Log("!pb", "Runner Page: {}".format(runnerPage))
    runnerPage = json.loads(runnerPage['response'])
    speedrunner_id = runnerPage['data']['id']   #Grab international username for current WR holder
    Parent.Log("!pb", "Runner ID is {}".format(speedrunner_id))
    return speedrunner_id
	
    
def getGame():
    #Pulls the json blob from twitch, and returns the Game (As a string), and the Title of the stream.
    Parent.Log("!pb", "Connecting to Twitch API to pull the game you're playing.")
    r = Parent.GetRequest("https://api.twitch.tv/helix/streams?user_login={}".format(Parent.GetChannelName()), headers)
    rJson = json.loads(r)       #Parent.GetRequest pulls information back as a string, we're converting it to a json object
    if rJson['status'] == 200:  # If successful response
        Live = 1
        GameJson = json.loads(rJson['response'])
        #Parent.Log("!pb", "GameJson: {}".format(GameJson))
        Game_Code = GameJson['data'][0]['game_id']
        #Parent.Log("!pb", str(Game_Code))
        #Twitch api stores games as an ID (######) we need a human readable game name
        r = Parent.GetRequest("https://api.twitch.tv/helix/games?id={}".format(Game_Code), headers)
        r = json.loads(json.loads(r)['response'])
        game = r['data'][0]['name']
        title = GameJson['data'][0]['title']
        Parent.Log("!pb", "Title is : {}".format(title))
        Parent.Log("!pb", "Game is {}".format(game))
        return game, title
    return -1, -1


def getCategories(game, TwitchTitle):
    #Uses the speedrun API to get a list of category names for the game being run
    #This functions returns a link to the leaderboard page, and the name of the category to print later...
    #Debating returning the blob
    Parent.Log("!pb", "Getting list of category names from speedrun.com.")
    CategoryPage = Parent.GetRequest("https://speedrun.com/api/v1/games/{}/categories".format(game), {})
    CategoryPage = json.loads(CategoryPage)
    if CategoryPage['status'] == 200:
        CategoryPage = json.loads(CategoryPage['response'])
        TwitchTitleUpper = TwitchTitle.upper()
        for each in CategoryPage['data']:
            Parent.Log("!pb", "checking for {} in Title.".format(each['name']))
            if each['name'].upper() in TwitchTitleUpper:
                for link in each['links']:
                    if link['rel'] == "leaderboard":
                        return link['uri'], each['name']
    else:   #Failed to load the categories page for the game
        Parent.Log("!pb", "{} has no categories page.".format(game))
        return -2, -2
    #If we found no matching category in the title of the stream
    Parent.Log("!pb", "Error pulling the categories for {}.".format(game))
    return -5, -5
    
def getRuns(LeaderboardURL):
    #Pull the list of runs from the speedrun api
    Leaderboard = Parent.GetRequest(LeaderboardURL, {})
    Leaderboard = json.loads(Leaderboard)
    if Leaderboard['status'] != 200:
        Parent.Log("There was an issue getting the leaderboard {}.".format(LeaderboardURL))
        return "Blame speedrun.com for being broken. :)"
    Leaderboard = json.loads(Leaderboard['response'])
    return Leaderboard['data']['runs']

def send_message(message):
    Parent.SendStreamMessage(message)
    returnScriptName = "PB"
Website = "https://speedrun.com/"
Description = "Pulls Personal Best for a Category when called with 'commandName Category'" #See Line 15
Creator = "AuroTheAzure"
Version = "1.0.1"

''' 
Notes:
    Currently only works with top 50 runners.  For some weird reason code can't pull back past runner...58 or so, so 50 to be safe.
    Please make sure the name on like 18 matches your speedrun.com username
    Cooldown on line 16 is in seconds.
    Match Category in Twitch Title to the Tab in hte main board. :) (Any% | World Peace | All Red Berries | 70 Star etc.
'''

commandName = "!pb"     #String to start the command
cooldown = 1            #Cooldown of the command in seconds
runner_name = "EnsgMaster"        #Runner name as it appears on speedrun.com/

import datetime         #For converting time from a number of seconds to a human readable format (1:23:45.67)
import json             #For quickly / easily parsing data from speedrun.com/


headers = {'Client-ID': 'umyyc7qkoxedtjir8wo50iinz6qzs8'}  #No touchey

def Init():
    return


def Execute(data):
    if data.GetParam(0) != commandName or Parent.IsOnCooldown(ScriptName, commandName) or not Parent.IsLive():
        #If we're not called with our command name, or we're on cooldown, quit.
        #Parent.Log("!pb", "The game is {}".format(game))
        return
    else:
        game, title = getGame()
        if game == -1 and title == -1:
            send_message("There was an issue grabbing the game / title from Twitch.")
            return
        gameURL = SpeedrunGame(game)
        url, category = getCategories(gameURL, title)
        Parent.Log("!pb", "url is {}; category is {}".format(url, category))
        if url == -5 and category == -5:            # This means the category wasn't found in the twitch title
            gameURL = CategoryExtensions(game)
            url, category = getCategories(gameURL, title)
            Parent.Log("!pb", "url is {}; category is {}".format(url, category))
        elif url == -2 and category == -2:          # This means the category page failed to load.
            send_message("Contact the creator, because your game is not currently supported.") #Gotta get more work somehow :)
            return
        runs = getRuns(url)
        runnerID = getRunnerId(runner_name)
        
        pbrun = {}
        for run in runs:
            #Parent.Log("!pb", str(run))
            id = run['run']['players'][0]['id']
            if id == runnerID:
                pbrun = run
                Parent.Log("!pb", str(pbrun))
                break
        Time = pbrun['run']['times']['primary_t']
        TimeParsed = datetime.timedelta(seconds=Time)
        TimeString = str(TimeParsed)
        while TimeString[0] == '0' or TimeString[0] == ':':
            TimeString = TimeString[1::]
        send_message("{} PB in {} {} is {}".format(runner_name, game, category, TimeString))
	return


def Tick():
    return


def SpeedrunGame(TwitchGameName):
    #TwitchGameName is Game according to Twitch
    if TwitchGameName == "Super Mario Odyssey":     #SMO Main board
        return "smo"
    elif TwitchGameName == "Super Mario 64":        #SM64 Main Board
        return "sm64"
    elif TwitchGameName == "Celeste":               #Celeste Main Board
        return "celeste"
    elif TwitchGameName == "Super Mario Sunshine":
        return "sms"
    elif TwitchGameName == "Yu-Gi-Oh! Forbidden Memories":
        return "yugiohfm"

def CategoryExtensions(TwitchGameName):
    #TwitchGameName is the Game according to Twitch
    if TwitchGameName == "Super Mario Odyssey":     #SMO Category Extensions
        return "smoce"
    elif TwitchGameName == "Super Mario 64":        #SM64 Category Extensions
        return "sm64memes"
    elif TwitchGameName == "Celeste":               #Celeste Category Extensions
        return "celeste_category_extensions"
    elif TwitchGameName == "Super Mario Sunshine":
        return "smsce"
    elif TwitchGameName == "Yu-Gi-Oh! Forbidden Memories":
        return "yugiohfmextensions"

def getRunnerId(speedrunner_name):
    #Get the runners ID from speedrun.com to query the speedrun API less.
    Parent.Log("!pb", "Pulling from speedrun.com/api/v1/users/{}".format(speedrunner_name))
    runnerPage = Parent.GetRequest("https://speedrun.com/api/v1/users/{}".format(speedrunner_name), {})
    runnerPage = json.loads(runnerPage)                     #Get speedrun.com data for user code
    Parent.Log("!pb", "Runner Page: {}".format(runnerPage))
    runnerPage = json.loads(runnerPage['response'])
    speedrunner_id = runnerPage['data']['id']   #Grab international username for current WR holder
    Parent.Log("!pb", "Runner ID is {}".format(speedrunner_id))
    return speedrunner_id
	
    
def getGame():
    #Pulls the json blob from twitch, and returns the Game (As a string), and the Title of the stream.
    Parent.Log("!pb", "Connecting to Twitch API to pull the game you're playing.")
    r = Parent.GetRequest("https://api.twitch.tv/helix/streams?user_login={}".format(Parent.GetChannelName()), headers)
    rJson = json.loads(r)       #Parent.GetRequest pulls information back as a string, we're converting it to a json object
    if rJson['status'] == 200:  # If successful response
        Live = 1
        GameJson = json.loads(rJson['response'])
        #Parent.Log("!pb", "GameJson: {}".format(GameJson))
        Game_Code = GameJson['data'][0]['game_id']
        #Parent.Log("!pb", str(Game_Code))
        #Twitch api stores games as an ID (######) we need a human readable game name
        r = Parent.GetRequest("https://api.twitch.tv/helix/games?id={}".format(Game_Code), headers)
        r = json.loads(json.loads(r)['response'])
        game = r['data'][0]['name']
        title = GameJson['data'][0]['title']
        Parent.Log("!pb", "Title is : {}".format(title))
        Parent.Log("!pb", "Game is {}".format(game))
        return game, title
    return -1, -1


def getCategories(game, TwitchTitle):
    #Uses the speedrun API to get a list of category names for the game being run
    #This functions returns a link to the leaderboard page, and the name of the category to print later...
    #Debating returning the blob
    Parent.Log("!pb", "Getting list of category names from speedrun.com.")
    CategoryPage = Parent.GetRequest("https://speedrun.com/api/v1/games/{}/categories".format(game), {})
    CategoryPage = json.loads(CategoryPage)
    if CategoryPage['status'] == 200:
        CategoryPage = json.loads(CategoryPage['response'])
        TwitchTitleUpper = TwitchTitle.upper()
        for each in CategoryPage['data']:
            Parent.Log("!pb", "checking for {} in Title.".format(each['name']))
            if each['name'].upper() in TwitchTitleUpper:
                for link in each['links']:
                    if link['rel'] == "leaderboard":
                        return link['uri'], each['name']
    else:   #Failed to load the categories page for the game
        Parent.Log("!pb", "{} has no categories page.".format(game))
        return -2, -2
    #If we found no matching category in the title of the stream
    Parent.Log("!pb", "Error pulling the categories for {}.".format(game))
    return -5, -5
    
def getRuns(LeaderboardURL):
    #Pull the list of runs from the speedrun api
    Leaderboard = Parent.GetRequest(LeaderboardURL, {})
    Leaderboard = json.loads(Leaderboard)
    if Leaderboard['status'] != 200:
        Parent.Log("There was an issue getting the leaderboard {}.".format(LeaderboardURL))
        return "Blame speedrun.com for being broken. :)"
    Leaderboard = json.loads(Leaderboard['response'])
    return Leaderboard['data']['runs']

def send_message(message):
    Parent.SendStreamMessage(message)
    return