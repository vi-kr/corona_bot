# -*- coding: utf-8 -*-

######## Import von Paketen ########
import os
import glob
import numpy
import pandas
import pickle
import locale
import random
import string
import logging
import pathlib
import discord
import requests
import subprocess
import matplotlib.pyplot as plt

from discord.ext import tasks
from discord.utils import get
from discord.ext.commands import Bot
from datetime import datetime, timedelta
from matplotlib.dates import DateFormatter

landCode = {
    'gesamt' : 16,
    'thüringen' : 15,
    'schleswig-holstein' : 14,
    'sachsen-anhalt' : 13,
    'sachsen' : 12,
    'saarland' : 11,
    'rheinland-pfalz' : 10,
    'nordrhein-westfalen' : 9,
    'niedersachsen' : 8,
    'mecklenburg-vorpommern' : 7,
    'hessen' : 6,
    'hamburg' : 5,
    'bremen' : 4,
    'brandenburg' : 3,
    'berlin' : 2,
    'bayern' : 1,
    'baden-württemberg' : 0,}

wochentag = {0 : "Montag",
             1 : "Dienstag",
             2 : "Mittwoch",
             3 : "Donnerstag", 
             4 : "Freitag", 
             5 : "Samstag",
             6 : "Sonntag",}

######## Hilfsfunktion zum Starten der Spider ########

async def startScrape():
      csvfiles = glob.glob(str(pathlib.Path(__file__).resolve().parents[1]) + os.path.sep + "data" + os.path.sep + "*.csv")
      if (str(pathlib.Path(__file__).resolve().parents[1])
                    + os.path.sep + "data"
                    + os.path.sep + datetime.now().strftime("%Y%m%d") + ".csv") not in csvfiles:
          scrape = subprocess.Popen(str(pathlib.Path(__file__).resolve().parents[1])
                                  + os.path.sep + "corona"
                                  + os.path.sep + "spiders"
                                  + os.path.sep + "fallzahlen.py")
          scrape.wait()
      else: logging.info(datetime.now().strftime("%Y/%m/%d %h:%m:%s") + "; Kein Update notwendig")

######## Parserfunktion für die Argumente ########

def argParse(argList):
    if argList == ['']:
        return({'': ''})
    dict = {}
    tmp = ''
    key = ''
    for arg in argList:
        if arg[0] == '-':
            if tmp != []:
                dict[key] = tmp
                tmp = ''
            key = arg 
            continue
        tmp = arg
    dict[key] = tmp
    return(dict)

######## Hilfsfunktion um aus dem DF nach Land auszuwählen ########

def getLandDf(df, land):
    return(df.loc[landCode[land.lower()], :])

######## Hilfsfunktion zum Updaten der Dateien ########
csvfiles = []
df = []

def readFiles():
    global csvfiles
    global df
    csvfiles = glob.glob(str(pathlib.Path(__file__).resolve().parents[1]) + os.path.sep + "data" + os.path.sep + "*.csv")
    df = pandas.concat([pandas.read_csv(fp, decimal = "+").assign(Date=os.path.basename(fp)[:-4]) for fp in csvfiles])
    df.columns.values[2]='Differenz'
    df.Anzahl = df.Anzahl.map(lambda cell: cell.translate(str.maketrans('', '', string.punctuation)))
    df.Differenz = df.Differenz.map(lambda cell: cell.translate(str.maketrans('', '', string.punctuation)))
    df.Fälle = df.Fälle.map(lambda cell: cell.translate(str.maketrans('', '', string.punctuation)))
    df.Tode = df.Tode.map(lambda cell: cell.translate(str.maketrans('', '', string.punctuation)))
    df.Anzahl = df.Anzahl.map(lambda cell: int(cell))
    df.Differenz = df.Differenz.map(lambda cell: int(cell))
    df.Fälle = df.Fälle.map(lambda cell: int(cell))
    df.Tode = df.Tode.map(lambda cell: int(cell))
    df.Date = df.Date.map(lambda cell: (datetime.strptime(cell, '%Y%m%d') - timedelta(days=1)))

impfdf = 0
def downloadImpfungen():
    global impfdf
    impf_url = "https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Daten/Impfquotenmonitoring.xlsx?__blob=publicationFile"
    q = requests.get(impf_url)
    filename = str(pathlib.Path(__file__).resolve().parents[1]) + os.path.sep + "data" + os.path.sep + "impfungen.xlsx"
    with open(filename,'wb') as f:
        f.write(q.content)
    impfdf = pandas.read_excel(filename, sheet_name="Impfungen_proTag").fillna(value=0)
    impfdf = impfdf[(impfdf.T != 0).any()]
    impfdf = impfdf[:impfdf[impfdf['Datum'] == 'Gesamt'].index[0]+1]

testdf = 0
def downloadTests():
    global testdf
    tests_url = "https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Daten/Testzahlen-gesamt.xlsx?__blob=publicationFile"
    r = requests.get(tests_url)
    filename = str(pathlib.Path(__file__).resolve().parents[1]) + os.path.sep + "data" + os.path.sep + "tests.xlsx"
    with open(filename,'wb') as f:
        f.write(r.content)
    testdf = pandas.read_excel(filename, sheet_name="1_Testzahlerfassung")
    testdf = testdf.drop(testdf.head(1).index)
    testdf = testdf.drop(testdf.tail(1).index)
    testdf.iloc[:,1] = testdf.iloc[:,1].map(lambda cell: int(cell))
    testdf.iloc[:,2] = testdf.iloc[:,2].map(lambda cell: int(cell))
    testdf.iloc[:,3] = testdf.iloc[:,3].map(lambda cell: float(cell))
    #testdf.iloc[:,0] = testdf.iloc[:,0].map(lambda cell: datetime.strptime(cell + '-1', "%W/%Y-%w"))
    
######## Hilfsfunktion zum Plotten ########

async def makePlot(land, over, fromTime, toTime):
          land = "Gesamt" if (land == None) else land.title()
          over = "Inzidenz" if (over == None) else over.title()
          if (fromTime == None): fromTime = "24.02.2021"
          if (toTime == None): toTime = datetime.now().strftime('%d.%m.%Y')
          print(land + " " + over + " " + fromTime + " " + toTime)
          mask = (df['Date'] >= datetime.strptime(fromTime,'%d.%m.%Y')) & (df['Date'] <= datetime.strptime(toTime,'%d.%m.%Y'))
          subdata = df.loc[mask]
          fig, ax = plt.subplots()
          date_form = DateFormatter("%d.%m.")
          ax.xaxis.set_major_formatter(date_form)
          x, y = zip(*sorted(zip(getLandDf(subdata, land).Date, getLandDf(subdata, land)[over]),key=lambda x: x[0]))
          plt.plot(x, y,
                   marker = "o", markerfacecolor = "k", markersize=3,
                   color='lightblue')
          plt.grid(color='lightgrey', linestyle='-', linewidth=1, alpha = 0.4)
          plt.title(land.title())
          every_nth = 2
          for n, label in enumerate(ax.xaxis.get_ticklabels()):
              if n % every_nth != 0:
                  label.set_visible(False)
          plt.ylabel(over.title())
          plt.savefig(str(pathlib.Path(__file__).resolve().parents[1]) + os.path.sep + "data" + os.path.sep + "plot.png", dpi=300)
    
async def plotTest():
          global testdf
          fig, ax = plt.subplots()
          x = testdf['Kalenderwoche']
          testsGesamt = testdf['Anzahl Testungen']/1000000
          testsPositiv =   testdf['Positiv getestet']/1000000
          plt.plot(x, testsGesamt, label = "Tests insgesamt")
          plt.plot(x, testsPositiv, label = "Positive Tests") 
          plt.fill_between(x, testsGesamt, testsPositiv, alpha = 0.4)
          plt.fill_between(x, testsPositiv, 0, alpha = 0.4)
          every_nth = int(len(x)/6)
          plt.legend(loc="upper left")
          for n, label in enumerate(ax.xaxis.get_ticklabels()):
              if n % every_nth != 0:
                  label.set_visible(False)
          plt.grid(color='lightgrey', linestyle='-', linewidth=1, alpha = 0.4)
          plt.title("Deutschland")
          plt.ylabel("Tests in Millionen")
          plt.xlabel("Kalenderwoche")
          plt.savefig(str(pathlib.Path(__file__).resolve().parents[1]) + os.path.sep + "data" + os.path.sep + "plot.png", dpi=300)

######## Hilfsfunktionen und -Variablen für das Ratespiel ########    

def getFirstKey(dictionary):
    for key in dictionary:
        return key
    raise IndexError

guessingAllowed = True
guesses = {}
nummerierung = {1 : "Erster",
                2 : "Zweiter",
                3 : "Dritter",
                4 : "Vierter",
                5 : "Fünfter",
                6 : "Sechster",
                7 : "Siebter",
                8 : "Acher",
                9 : "Neunter",
                10 : "Zehnter",}

async def guessOutput(channelID):
    global guesses
    global sent
    try:
        guesses = load_dict()
    except: pass
    message = ""
    if guesses != {}:
        diffs = {}
        gestern = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        inzidenzGestern = df.loc[df.Date == gestern]["Inzidenz"].tolist()[landCode["gesamt"]]
        print(inzidenzGestern)
        for key in guesses:
            guesses[key] = int(guesses[key])
            diffs[key] = abs(int(inzidenzGestern) - guesses[key])
        sorted_guesses = {}
        sorted_keys = sorted(diffs, key=diffs.get)
        for key in sorted_keys:
            sorted_guesses[key] = guesses[key]
        message += "Die Inzidenz liegt jetzt bei " + str(inzidenzGestern) + ". \n"
        print(max(df["Inzidenz"][landCode["gesamt"]].tolist()))
        if inzidenzGestern == max(df["Inzidenz"][landCode["gesamt"]].tolist()):
            message += "Das ist in der von mir aufgezeichneten Zeit ein Rekordhoch! \n"
        message += "\n"
        message += "Ergebnis des Inzidenz-Ratens: \n"
        i = 0
        prevDiff = -1
        for userID in sorted_guesses:
            user = await serverID.fetch_member(userID)
            if diffs[userID] != prevDiff:
                i += 1
            message += (nummerierung[i] + " Platz: " + user.mention
                                        + "["+ user.name + "] hat " + str(sorted_guesses[userID])
                                        + " geraten (Differenz von " + str(diffs[userID]) + ").\n")
            prevDiff = diffs[userID]
        guesses = {}
        os.remove(str(pathlib.Path(__file__).resolve().parents[1]) + os.path.sep + "data" + os.path.sep + "guesses.pkl")
        await removeMeister(channelID)
        await makeMeister(await serverID.fetch_member(getFirstKey(sorted_guesses)), channelID)
    else:
        message += "Niemand hat versucht die Inzidenz zu erraten."
    await channelID.send(message)
    await sent.edit(content="Bis jetzt hat noch niemand versucht die Inzidenz zu erraten.") 
    
async def makeMeister(member, userID):
    role = get(userID.guild.roles, name="Meister der Inzidenzen")
    await member.add_roles(role)

async def removeMeister(userID):
    role = get(userID.guild.roles, name="Meister der Inzidenzen")
    for member in userID.guild.members:
        try:
            await member.remove_roles(role)
        except: pass

def save_dict(obj):
    with open(str(pathlib.Path(__file__).resolve().parents[1]) + os.path.sep + "data" + os.path.sep + "guesses.pkl", 'wb') as f:
        pickle.dump(obj, f)

def load_dict():
    with open(str(pathlib.Path(__file__).resolve().parents[1]) + os.path.sep + "data" + os.path.sep + "guesses.pkl", 'rb') as f:
        return pickle.load(f)
    
def save_messageID(obj):
    with open(str(pathlib.Path(__file__).resolve().parents[1]) + os.path.sep + "data" + os.path.sep + "message.pkl", 'wb') as f:
        pickle.dump(obj, f)

def load_messageID():
    with open(str(pathlib.Path(__file__).resolve().parents[1]) + os.path.sep + "data" + os.path.sep + "message.pkl", 'rb') as f:
        return pickle.load(f)
      

######## Initialisierung des Bot-Clients ########

locale.setlocale(locale.LC_ALL, '')
intents = discord.Intents.all()
client = discord.ext.commands.Bot(command_prefix='-', intents=intents)
serverID = 0
channelID = 0
sent = 0

async def setupServer():
    global serverID
    global channelID
    serverID = await client.fetch_guild('SERVER_ID')
    channelID = client.get_channel('CHANNEL_ID')

######## Aktionen beim Einloggen und Definition der Update-Taskloop ########

@client.event
async def on_ready():
    global guesses
    global sent
    global channelID
    await setupServer()
    readFiles()
    try:
        downloadImpfungen()
    except: await channelID.send("Beim Herunterladen der Impfdaten ist etwas schief gelaufen.")
    try:
        downloadTests()
    except: await channelID.send("Beim Herunterladen der Testdaten ist etwas schief gelaufen.")
    try:
        guesses = load_dict()
    except: pass
    try:
        messageID = load_messageID()
        sent = await channelID.fetch_message(messageID)
    except Exception as e:
        print(e)
        if guesses == {}:
            sent = await channelID.send("Bis jetzt hat noch niemand versucht die Inzidenz zu erraten.")
        else:
            descr = "Aktuelle Vorhersage-Versuche: \n \n"
            for userID in guesses:
                user = await serverID.fetch_member(userID)
                descr += (user.display_name + "["+ user.name + "] hat " + str(guesses[userID]) 
                          + " geraten.\n")
            sent = await channelID.send(descr)
        await sent.pin()
        save_messageID(sent.id)
    print('We have logged in as {0.user}'.format(client))
    updateLoop.start()
 
@tasks.loop(minutes=60)
async def updateLoop():
    global guessingAllowed
    channelID = client.get_channel('CHANNEL_ID')
    if datetime.now().hour == 12:
        await startScrape()
        if (datetime.today().weekday() != 5 and datetime.today().weekday() != 6):
            downloadImpfungen()
            print(impfdf)
        if datetime.today().weekday() == 3:
            downloadTests()
            print(testdf)
        readFiles()
        await channelID.send("Routine-Update abgeschlossen. Meine Daten sollten jetzt auf dem Stand vom " + datetime.now().strftime("%d.%m.%Y") + " sein.")
        await guessOutput(channelID)
        guessingAllowed = True
    elif datetime.now().hour < 11 and datetime.now().hour > 3: guessingAllowed = False
    else: guessingAllowed = True


######## Error-Handling ########

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.UnexpectedQuoteError):
        await ctx.channel.send("Bitte keine Anführungszeichen in Befehlen verwenden.")
    elif isinstance(error, discord.ext.commands.UserInputError):
        await ctx.channel.send("Fehler in \"{}\". Entweder du hast Eingaben vergessen oder diese sind im falschen Format.".format(ctx.message.content))
    else: print(error)

######## Befehle zur Interaktion mit dem Bot ########
    
@client.command(name='impfo',pass_context = True, help='Kurze Info zum Impfgeschehen.')    
async def impfo(ctx):
    await ctx.channel.send("Am " + wochentag[datetime.strptime(impfdf["Datum"].iloc[-2], "%d.%m.%Y").weekday()]
                           + " wurden in Deutschland "
                           + locale.format_string("%d", int(impfdf["Gesamtzahl verabreichter Impfstoffdosen"].iloc[-2]), grouping=True)
                           + " Impfdosen verabreicht. Insgesamt sind es damit "
                           + locale.format_string("%d", int(impfdf["Gesamtzahl verabreichter Impfstoffdosen"].iloc[-1]), grouping=True)
                           + ".\n"
                           + "Ihre zweite Impfdosis erhalten haben nun "
                           + locale.format_string("%d", int(impfdf["Zweitimpfung"].iloc[-1]), grouping=True)
                           + " Personen("
                           + f'{int(impfdf["Zweitimpfung"].iloc[-1])/830200:.2f}'
                           + "%).")

@client.command(name='guess',pass_context = True, help='Erraten der Inzidenz für den nächsten Tag.')
async def guess(ctx, guess):
    global guesses
    global guessingAllowed
    global messageID
    if not guessingAllowed:
        ctx.channel.send("Raten ist erst wieder nach der Auflösung erlaubt.")
    else:
        userID = ctx.message.author.id
        try:
            guess = int(guess)
        except:
            await ctx.channel.send("Die Inzidenz sollte eine Zahl zwischen 0 und 9999 sein.")
            return
        if guess>=0 and guess<=9999:
            for key, value in guesses.items():
                if guess == value:
                    if userID != key:
                        user = await serverID.fetch_member(key)
                        await ctx.channel.send(user.display_name + " hat bereits " + str(guess) + " geraten. Du musst etwas anderes raten.")
                        return  
            else:
                guesses[userID] = guess
                await ctx.channel.send("Du hast {guess} geraten.".format(guess=guess))
                save_dict(guesses)
                descr = "Aktuelle Vorhersage-Versuche: \n \n"
                for userID in guesses:
                    user = await serverID.fetch_member(userID)
                    descr += (user.display_name + "["+ user.name + "] hat " + str(guesses[userID]) 
                      + " geraten.\n")
                await sent.edit(content=descr)
        else: await ctx.channel.send("Die Inzidenz sollte eine Zahl zwischen 0 und 9999 sein.")

@client.command(name='briefing',pass_context = True, help='Bringt den Minister auf den neusten Stand.')
async def briefing(ctx):
    if (ctx.message.author.id == 'OWNER_ID'):
        downloadImpfungen()
        downloadTests()
        await startScrape()
        readFiles()
        await ctx.channel.send("Meine Daten sind jetzt auf dem neusten Stand.")
    else:
        await ctx.channel.send("Du bist dazu nicht berechtigt.")

@client.command(name='graph',pass_context = True, help='Graphische Darstellung der Lage.')
async def graph(ctx, *, arg=""):
    argList = arg.split(sep = " ")
    argDict = argParse(argList)
    await makePlot(land = argDict.get('-l'),
                   over = argDict.get('-o'),
                   fromTime = argDict.get('-f'),
                   toTime = argDict.get('-t')) 
    await ctx.channel.send(file=discord.File(str(pathlib.Path(__file__).resolve().parents[1])
                                             + os.path.sep + "data"
                                             + os.path.sep + "plot.png"))

@client.command(name='tests',pass_context = True, help='Graphische Darstellung der Tests.')
async def tests(ctx):
    await plotTest()
    await ctx.channel.send(file=discord.File(str(pathlib.Path(__file__).resolve().parents[1])
                                             + os.path.sep + "data"
                                             + os.path.sep + "plot.png"))

    
@client.command(name='info', pass_context = True, help='Kurzer Lagebericht')
async def info(ctx, *, arg = ""):
    argList = arg.split(sep = " ")
    argDict = argParse(argList)
    if argDict == {'': ''}: land = "gesamt"
    else:
        try: land = argDict["-l"] if (argDict["-l"] != None) else "gesamt"
        except KeyError: land = "gesamt"
    gestern = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    faelleGestern = df.loc[df.Date == gestern]["Differenz"].tolist()[landCode[land]]
    if "--vergleich" in ctx.message.content or "-v" in ctx.message.content:
        VorEinerWoche = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=8)
        faelleVorEinerWoche = df.loc[df.Date == VorEinerWoche]["Differenz"].tolist()[landCode[land]]
        differenz = faelleGestern - faelleVorEinerWoche
        await ctx.channel.send("Gestern gab es in "
                               + ("Deutschland" if (land == "gesamt") else land.title())
                               + " "
                               + str(faelleGestern)
                               + " neue Fälle. Das sind "
                               +  str(abs(differenz))
                               + (" weniger" if differenz<0 else " mehr")
                               + " als letzte Woche. \n"
                               + "Die liegt die 7-Tage-Inzidenz jetzt bei "
                               + str(df.loc[df.Date == gestern]["Inzidenz"].tolist()[landCode[land]])
                               + ".")
    else:
        await ctx.channel.send("Gestern gab es in "
                               + ("Deutschland" if (land == "gesamt") else land.title())
                               + " "
                               + str(faelleGestern)
                               + " neue Fälle, damit liegt die 7-Tage-Inzidenz jetzt bei "
                               + str(df.loc[df.Date == gestern]["Inzidenz"].tolist()[landCode[land]])
                               + ".")

@client.command(name='zensur', help='Entfernt die letzten Nachrichten. Standard sind 10.')
async def zensur(ctx, amount = 10):
    if (message.author.id == 'OWNER_ID'):
        await ctx.channel.purge(limit=amount)
    else:
        await ctx.channel.send("Du bist dazu nicht berechtigt.")


client.run('TOKEN')
