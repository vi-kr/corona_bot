import discord
from random import randint
from discord.ext.commands import Bot

client = discord.ext.commands.Bot(command_prefix='-')

antworten = ["Nein.", "Frag doch einfach noch mal!", "Eines Tages vielleicht.", "Ja."]
wasAntworten = ["Gar Nichts.", "Nichts.", "Alles.", "Frag doch einfach noch mal!", "Das kann ich dir nicht sagen."]
wannAntworten = ["Nie.", "Jetzt.", "In weiter Zukunft.", "In naher Zukunft",  "Frag doch einfach noch mal!"]
warumAntworten = ["Frag doch einfach noch mal!", "Einfach so.", "Ohne Grund."]
wieAntworten = ["Frag doch einfach noch mal!", "Einfach so.", "Das kann ich dir nicht sagen."]

def orakel(message):
    if "warum" == message[25:30] or "wieso" == message[25:30] or "weshalb" == message[25:32]:
        return(warumAntworten[randint(0, len(warumAntworten)-1)])
    elif "was" == message[25:28]:
        return(wasAntworten[randint(0, len(wasAntworten)-1)])
    elif "wann" == message[25:29]:
        return(wannAntworten[randint(0, len(wannAntworten)-1)])
    elif "wie" == message[25:28]:
        return(wieAntworten[randint(0, len(wieAntworten)-1)])
    else: return(antworten[randint(0, len(antworten)-1)])

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    global EmojiList
    EmojiList = client.emojis

@client.event
async def on_message(message):
    if message.author.bot or message.content.startswith("!"):
        pass
    elif message.content.startswith("Oh magische Miesmuschel, "):
        await message.channel.send(orakel(message.content))
    elif (("schere" in message.content) or ("Schere" in message.content)):
        if (message.author.id == 411474378761437184):
            await message.channel.send("Ich wähle Papier. Du gewinnst.")
        else: 
            await message.channel.send("Ich wähle Stein. Du verlierst.")
    elif (("stein" in message.content) or ("Stein" in message.content)):
        if (message.author.id == 411474378761437184):
            await message.channel.send("Ich wähle Schere. Du gewinnst.")
        else: 
            await message.channel.send("Ich wähle Papier. Du verlierst.")
    elif (("papier" in message.content) or ("Papier" in message.content)):
        if (message.author.id == 411474378761437184):
            await message.channel.send("Ich wähle Stein. Du gewinnst.")
        else: 
            await message.channel.send("Ich wähle Schere. Du verlierst.")
    else: await message.add_reaction(EmojiList[randint(0, len(EmojiList)-1)])
    

client.run('ODE1MzQ2NDQ2MzkxMDUwMjcx.YDrEjQ.tt_tnSS23qzCb9Qvb8WB1GksxWE')