""
import discord
from discord.ext.commands import Bot
from discord.ext import commands
import asyncio
import time
from random import randint, choice
import sqlite3
import logging
import re


Client = discord.Client(command_prefix="")
client = commands.Bot(command_prefix="")

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)



IA = "Isabel [IA]#6016"
dbPath = "./database/data.db"

############################################################################################################################################
########################################################### IA #############################################################################
############################################################################################################################################

def safeData(text):
    a = ""
    b = re.compile("[^']").findall(text)
    for letter in b:
        a += letter
    return a

def executeCommand(f):
    global dbPath
    conn = sqlite3.connect(dbPath)
    c = conn.cursor()
    try:
        c.execute(f)
    except sqlite3.OperationalError as E:
        print("Requete plante", f)
        print(E)
        return (False)
    row = c.fetchall()
    conn.commit()
    conn.close()
    return (row)

def setAuthorizationLevel(idServer, idPlayer, authorizationLevel):
    f = "UPDATE player SET authorizationLevel = {} WHERE idPlayer = '{}' AND idServer = '{}'".format(str(authorizationLevel), idPlayer, idServer)
    executeCommand(f)

def getAuthorizationLevel(message):
    serverId = message.server.id
    idPlayer = message.author.id
    f = "SELECT authorizationLevel FROM player WHERE idServer = '{}' AND idPlayer = '{}'".format(serverId, idPlayer)
    row = executeCommand(f)
    if (row == False) or len(row) == 0:
        return (False)
    try:
        return (row[0][0])
    except Exception as E:
        print(E)

def insertPlayer(message):
    idPlayer = message.author.id
    name = message.author.name
    name = safeData(name)
    idServer = message.server.id
    f = "SELECT name FROM player where idPlayer = '{}' AND idServer = '{}'".format(idPlayer, idServer)
    row = executeCommand(f)
    try:
        if row is False:
            return
        if len(row) == 0:
            f = "INSERT INTO player(idPlayer, name, idServer, authorizationLevel) VALUES('{}', '{}', '{}', 0)".format(idPlayer, name, idServer)
            executeCommand(f)
        else:
            f = "UPDATE player SET name = '{}' WHERE idPlayer = '{}' AND idServer = '{}'".format(name, idPlayer, idServer)
            executeCommand(f)
    except Exception as E:
        print ("Insert Player Exception : ", E)


def getName(idPlayer, idServer):
    f = "SELECT name FROM player WHERE idPlayer = '{}' AND idServer = '{}'".format(idPlayer, idServer)
    row = executeCommand(f)
    try:
        return (row[0][0])
    except:
        return (False)

def getBannedWords(idServer):
    f = "SELECT word FROM bannedWords WHERE idServer = '{}'".format(idServer)
    row = executeCommand(f)
    return (row)

def getEditsWords(idServer):
    f = "SELECT wordBan, wordEdit from editWords WHERE idServer = '{}'".format(idServer)
    row = executeCommand(f)
    wordBan = list()
    editWords = list()
    for truc in row:
        wordBan.append(truc[0])
        editWords.append(truc[1])
    return wordBan, editWords

def insertEditWords(idServer, wordBan, wordEdit):
    f = "INSERT INTO editWords(idServer, wordBan, wordEdit) VALUES('{}', '{}', '{}')".format(idServer, wordBan, wordEdit)
    executeCommand(f)

def insertBannedWord(idServer, bannedWord):
    f = "INSERT INTO bannedWords(idServer, word) VALUES('{}', '{}')".format(idServer, bannedWord)
    executeCommand(f)
    
@client.event
async def on_message(message):
    insertPlayer(message)
    authorizationLevel = getAuthorizationLevel(message)
    bannedWords = getBannedWords(message.server.id)
    editWord1, editWord2 = getEditsWords(message.server.id)
    for word in bannedWords:
        if word[0] in message.content.lower():
            print("Message a detruire!")
            await client.delete_message(message)
            print("Message a detruire!")
            return
    i = 0
    while (i < len(editWord1)):
        if editWord1[i] in message.content.lower():
            position = message.content.find(editWord1[i])
            message.content = message.content[0: position] + editWord2[i] + message.content[position + len(editWord1[i]):]
            await client.edit_message(message, message.content)
            print("Message a editer!")
        i += 1


    if (message.content.lower().startswith('!sansami')):
        await client.send_message(message.channel, "C'est triste que tu sois sans ami. Mais je m'en branle.")
        
    if (message.content.lower().startswith("!ancien")):
        time = message.author.joined_at
        s = "Vous avez rejoint le serveur le " + time.strftime("%Y-%m-%d %H:%M:%S")
        await client.send_message(message.channel, s)

    if (message.content.lower().startswith("!server")):
        nb_member = str(message.server.member_count)
        large = str(message.server.large)
        owner = message.server.owner
        owner = owner.name
        verification_level = str(message.server.verification_level)
        afk_timeout = str(message.server.afk_timeout)
        region = str(message.server.region)
        lroles = message.server.roles
        name = message.server.name
        created_at = message.server.created_at.strftime("%Y-%m-%d %H:%M:%S")
        s = "Le server a été crée le " + created_at
        s += "\nLe créateur du serveur se nomme: " + owner
        s += "\nCe serveur est large: " + large
        s += "\nIl possède " + nb_member + " membres"
        s += "\nLe serveur est hébergé ici: " + str(region)
        s += "\nEt il possède un niveau de vérification de " + verification_level
        s += "\nIl time out si vous ne parlez pas pendant " + afk_timeout + " s"
        s += "\nIl possède la liste des rôles suivant: "
        for roles in lroles:
            s += "\t" + str(roles)
        await client.send_message(message.channel, s)
        
    
    if authorizationLevel < 3:
        return
    if (message.content.lower().startswith("!replace ")):
        try:
            print("debut replace")
            message.content = message.content[len("!replace "):]
            tab = message.content.split('|')
            firstWord = tab[0]
            secondWord = tab[1]
            insertEditWords(message.server.id, firstWord, secondWord)
            await client.send_message(message.channel, "Effectué!")
            print("fin replace")
        except Exception as E:
            print(E)
            await client.send_message(message.channel, "usage: !replace badWord|goodWord")
    if (message.content.startswith("!ban ")):
        try:
            print("debut ban")
            tab = message.content.split(' ')
            bannedWord = tab[1]
            insertBannedWord(message.server.id, bannedWord)
            await client.send_message(message.channel, "Effectué!")
            print("fin ban")
        except Exception as E:
            print(E)
            await client.send_message(message.channel, "!usage: !ban badWord")
    if (message.content.startswith("!setLevel ")):
        try:
            print("debut setLevel")
            tab = message.content.lower().split(' ')
            idPlayer = safeData(tab[1])
            clientName = getName(idPlayer, message.server.id)
            if not clientName:
                await client.send_message(message.channel, "Erreur, l'usager n'existe pas!")                
            newAuth = int(safeData(tab[2]))
            if newAuth > 4 or newAuth < 0:
                await client.send_message(message.channel, "Erreur: le level d'autorisation doit-être compris entre 0 et 4.")
                return
            setAuthorizationLevel(message.server.id, idPlayer, newAuth)
            await client.send_message(message.channel, "L'user {} a maintenant un level d'accréditation : {}".format(clientName, str(newAuth)))
            print("fin setLevel")
        except Exception as E:
            print("Exception in setAuthorizationLevel: ", E)
            await client.send_message(message.channel, "Usage: !setAuthorizationLevel idPlayer authorizationLevel")
            return
    if (message.content.lower().startswith("!delete ")):
        idMessage = message.content.lower()[len("!delete "):]
        await client.delete_message(message)
        await client.delete_message(idMessage)
                
        
    if (message.content.lower().startswith("!getname")):
        idServer = message.server.id
        s = ""
        for server in client.servers:
            if (server.id == idServer):
                for users in server.members:
                    s += users.name + "\n"
                break
        print(s)
        with open("./trigger.txt", 'w+') as f:
            f.write(s)
        await client.send_message(message.channel, s)
        return
            
            
    
if __name__ == '__main__':
    import sys
    try:
        TOKEN = sys.argv[1]
    except:
        print('USAGE: python3 bot.py TOKENBOT')
        sys.exit(1)
    client.run(TOKEN)
