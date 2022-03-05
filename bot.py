# bot.py
import os
import math
import requests
import json
import discord
import psycopg2
from discord.ext import commands
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2 import sql
intents = discord.Intents.all()

load_dotenv()

bot = commands.Bot(command_prefix='!',intents=intents)


con = psycopg2.connect(
    dbname=os.getenv('dbNAME'),
    user=os.getenv('dbUSER'),
    host=os.getenv('dbHOST'),
    password=os.getenv('dbPASS'),
    port=os.getenv('dbPORT'))
con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = con.cursor()


def createUserbase():
    cur.execute(sql.SQL("CREATE TABLE registered_users (playerID serial PRIMARY KEY, userIGN varchar, discordID varchar);")
    )


def new_bracket(name):

    cur.execute(sql.SQL("CREATE TABLE {} (playerID serial PRIMARY KEY, name varchar, totalScore int);").format(
        sql.Identifier(name))
    )

def drop_bracket(name):
    cur.execute(sql.SQL("DROP TABLE {};").format(
        sql.Identifier(name))
    )


APIKEY = os.getenv('ERBS_TOKEN')


def get_game(gameid):
    headers = {
        'accept': 'application/json',
        'x-api-key': 'Q1bnTctw88aZmijZ7zOYR8yTOXkpeddC2Kfy2DAv',
    }

    response = requests.get('https://open-api.bser.io/v1/games/{}'.format(gameid), headers=headers)
    json_data = json.loads(response.text)
    game = type(json_data['userGames'])
    players = []
    for games in json_data['userGames']:
        if games['killerUserNum2'] is not 0:
            players.append([games['nickname'], games['gameRank'], games['killMonsters'], games['playerKill'], games['killer'], games['killer2']])
        elif games['killerUserNum'] is not 0:
            players.append([games['nickname'], games['gameRank'], games['killMonsters'], games['playerKill'], games['killer']])
        else:
            players.append([games['nickname'], games['gameRank'], games['killMonsters'], games['playerKill'], 'None'])
    print(game)
    print(players)
    return players


TOKEN = os.getenv('DISCORD_TOKEN')


@bot.command(name='delete_bracket', help='Create a new table by providing a name to store results of games from a set')
@commands.has_role('ADMIN')
async def bracket(ctx, name: str):
    drop_bracket(name)
    await ctx.send("Deleted a new table with the name: {}".format(name))


@bot.command(name='create_bracket', help='Create a new table by providing a name to store results of games from a set')
@commands.has_role('ADMIN')
async def bracket(ctx, name: str):
    new_bracket(name)
    await ctx.send("Created a new table with the name: {}".format(name))


@bot.command(name='save_game', help='Saves the results of a game given a gameID and table name. Call command with !save_game gameID tablename')
@commands.has_role('ADMIN')
async def save(ctx, gameid: int, tablename: str):
    game = get_game(gameid)
    embed = discord.Embed(title="Results", description="Game: {}".format(gameid),color=0x00ff00)
    plyrs = [None] * len(game)
    for plyr in game:
        plyrs[plyr[1]-1] = plyr
    print(plyrs)
    for games in plyrs:
        response = cur.execute(sql.SQL("INSERT INTO {} (name, totalscore) VALUES(%s, %s)".format(tablename)), [games[0], games[1]])

        if games[1] == 1:
            embed.add_field(name=":first_place: {}".format(games[0]), value="\u200b".format(games[1]), inline=False)
        elif games[1] == 2:
            embed.add_field(name=":second_place: {}".format(games[0]), value="\u200b".format(games[1]), inline=False)
        elif games[1] == 3:
            embed.add_field(name=":third_place: {}".format(games[0]), value="\u200b".format(games[1]), inline=False)
        else:
            embed.add_field(name="{}".format(games[0]), value="Place: {}".format(games[1]), inline=False)

    await ctx.send(embed=embed)


@bot.command(name='register', help='Use to link your ERBS ingame name to your Discord username. Call with !register ingamename')
async def register(ctx, name: str):
    username = name
    await ctx.message.delete()
    cur.execute("SELECT * FROM registered_users WHERE discordid = %s;", [str(ctx.author)])
    if cur.fetchone() is not None:
        await ctx.send("{}, you have already registered an ingame name, please contact support ".format(ctx.message.author.mention))
        return
    else:
        cur.execute("SELECT * FROM registered_users WHERE userign = %s;", [username])
        if cur.fetchone() is not None:
            await ctx.send("{}, that username is already registered, please contact an admin if you think this is a mistake.".format(ctx.message.author.mention))
            return
    cur.execute(sql.SQL("INSERT INTO registered_users (userign, discordid) VALUES (%s, %s);"), [username, str(ctx.author)])
    member = ctx.author
    role = discord.utils.get(member.guild.roles, name="Member")
    await member.add_roles(role)
    return


@bot.command(name='setupUSERS', help='create user database')
async def setupUSERS(ctx):
    createUserbase()
    await ctx.send("Setup of user database complete")


@bot.command(name='team', help='Declare a team. Must @ all members of the team with the command. ex: !team @yourself @teammate1 @teammate2')
@commands.has_role('Member')
async def team(ctx, *members: str):
    teammates = []
    teamname = ""
    print(members)
    for word in members[3:]:
        teamname += " "+ word
        print(word)
    print(teamname[1:])
    teamname = teamname[1:]
    if len(members) < 4:
        await ctx.send("{}, please one include 3 members and a team name..".format(ctx.message.author.mention))
        await ctx.message.delete()
        return
    if len(teamname) < 4 or len(teamname) > 17:
        await ctx.send("{}, team names must be between 4 and 17 characters.".format(ctx.message.author.mention))
        await ctx.message.delete()
        return
    cur.execute(sql.SQL("SELECT * FROM registered_teams WHERE teamname = %s"), [teamname])
    if cur.fetchone() is not None:
        await ctx.send("{}, that team name is already in use".format(ctx.message.author.mention))
        await ctx.message.delete()
        return
    print(teamname)
    for member in members[:3]:
        if member[2] is '!':
            user = await bot.fetch_user(int(member[3:-1]))
        else:
            user = await bot.fetch_user(int(member[2:-1]))
        print(int(member[3:-1]), " ",member[2:-1])
        print(user)
        cur.execute(sql.SQL("SELECT teamid FROM registered_users WHERE discordid = %s and teamid != null"), [str(user)])
        if cur.fetchone() is not None:
            await ctx.send("User {} is already in a team. A player can only be in 1 team at a time.".format(user))
            await ctx.message.delete()
            return
        cur.execute(sql.SQL("SELECT teamid FROM registered_users WHERE discordid = %s"), [str(user)])
        if cur.fetchone() is None:
            await ctx.send("User {} is not registered. Ensure all players are registered before forming a team.".format(user))
            await ctx.message.delete()
            return
        #if member[3:-1] in teammates:
            #await ctx.send("{}, please do not include the same teammate more than once. Try again.".format(ctx.message.author.mention))
            #return
        else:
            if member[2] is '!':
                teammates.append(member[3:-1])
            else:
                teammates.append(member[2:-1])
    if len(teammates) < 3:
        await ctx.send("{}, please include all team members (including yourself).".format(ctx.message.author.mention))
        return
    cur.execute(sql.SQL("INSERT INTO registered_teams (player1,player2,player3,registrationid, v1,v2,v3, teamname) VALUES (%s, %s, %s,%s,%s,%s,%s,%s);"),
                [teammates[0], teammates[1], teammates[2], ctx.message.id, False, False, False, teamname])
    await ctx.message.add_reaction('\u2705')
    await ctx.message.add_reaction('\u274C')

@bot.command(name='disband', help='disband your team to form a new one. Click the correct reaction to confirm.')
async def disband(ctx):
    await ctx.message.add_reaction('\u2705')
    await ctx.message.add_reaction('\u274C')

@bot.command(name='unregister', help='Disconnect your IGN from Discord.')
async def unregister(ctx):
    await ctx.message.add_reaction('\u2705')
    await ctx.message.add_reaction('\u274C')

@bot.event
async def on_raw_reaction_add(payload):
    print(payload)
    if payload.member.bot:
        return
    message = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
    if message.content.startswith('!disband'):
        if payload.emoji.name == "✅":
            cur.execute(sql.SQL("SELECT player1, player2, player3 FROM registered_teams WHERE player1 = %s or player2 = %s or player3 = %s"),
                        [str(payload.user_id), str(payload.user_id), str(payload.user_id)])
            z = cur.fetchone()
            print(z)
            for id in z:
                mem = payload.member.guild.get_member(int(id))
                role = discord.utils.get(payload.member.guild.roles, name="Registered")
                await mem.remove_roles(role)
            await message.delete()
            cur.execute(sql.SQL("DELETE FROM registered_teams WHERE player1 = %s or player2 = %s or player3 = %s"),
                        [str(payload.user_id), str(payload.user_id), str(payload.user_id)])
        if str(payload.emoji.name) == "❌":
            await message.delete()

    if message.content.startswith('!unregister'):
        if payload.emoji.name == "✅":
            cur.execute(sql.SQL("DELETE FROM registered_users WHERE discordid = %s"),
                        [payload.member.name+"#"+payload.member.discriminator])
            mem = payload.member
            role = discord.utils.get(payload.member.guild.roles, name="Member")
            await mem.remove_roles(role)
            await message.delete()
        if str(payload.emoji.name) == "❌":
            await message.delete()




    if message.content.startswith('!team'):
        cur.execute(sql.SQL("SELECT * FROM registered_teams WHERE registrationid = %s"), [str(payload.message_id)])
        z = cur.fetchone()
        print(z)
        if str(payload.user_id) in z:
            if payload.emoji.name == "✅":
                print("found emoji check")
                if str(payload.user_id) == z[1]:
                    cur.execute(sql.SQL("UPDATE registered_teams SET v1 = True WHERE teamid = %s"), [z[0]])
                if str(payload.user_id) == z[2]:
                    cur.execute(sql.SQL("UPDATE registered_teams SET v2 = True WHERE teamid = %s"), [z[0]])
                if str(payload.user_id) == z[3]:
                    cur.execute(sql.SQL("UPDATE registered_teams SET v3 = True WHERE teamid = %s"), [z[0]])
            if str(payload.emoji.name) == "❌":
                print("found emoji x")
                cur.execute(sql.SQL("DELETE FROM registered_teams WHERE teamid = %s"), [z[0]])
                await message.delete()
                return
            cur.execute(sql.SQL("SELECT * FROM registered_teams WHERE registrationid = %s AND v1 = True AND v2 = True AND v3 = True"), [str(payload.message_id)])
            if cur.fetchone() is not None:
                for mems in z[1:4]:
                    print(mems, type(mems), int(mems))
                    mem = payload.member.guild.get_member(int(mems))
                    print(mem)
                    role = discord.utils.get(payload.member.guild.roles, name="Registered")
                    await mem.add_roles(role)
                await message.delete()
                return

    if message.content.startswith('React to this') or message.content.startswith('react to this'):
        if message.channel.name == "signups":
            teststr = str(payload.user_id)
            cur.execute(sql.SQL("SELECT teamid FROM registered_teams WHERE player1 = %s or player2 = %s or player3 = %s"), [teststr, teststr, teststr])
            temp = cur.fetchone()
            cur.execute(sql.SQL("SELECT teamid FROM signup WHERE teamid = %s"), [temp])
            if cur.fetchone() is not None:
                print('returning')
                return
            else:
                cur.execute(sql.SQL("INSERT INTO signup (teamid) VALUES (%s);"), [temp])


@bot.command(name='drop', help='drop a group from signups')
async def drop(ctx, mem):
    print(mem)
    if mem[2] is "!":
        cur.execute(sql.SQL("SELECT teamid FROM registered_teams WHERE player1=%s or player2=%s or player3=%s"), [mem[3:-1], mem[3:-1] ,mem[3:-1]])
        teamid = cur.fetchone()
        print(teamid[0])
        cur.execute(sql.SQL("DELETE FROM signup WHERE teamid=%s"),
                    [teamid[0]])
    else:
        cur.execute(sql.SQL("SELECT teamid FROM registered_teams WHERE player1=%s or player2=%s or player3=%s"),
                    [mem[2:-1], mem[2:-1], mem[2:-1]])
        teamid = cur.fetchone()
        print(teamid[0])
        cur.execute(sql.SQL("DELETE FROM signup WHERE teamid=%s"),
                    [teamid[0]])

@bot.command(name='ats', help='Give yourself a spectator role')
@commands.has_role('ADMIN')
async def ats(ctx):
    print(ctx)
    cur.execute(sql.SQL("SELECT player1, player2, player3, teamname FROM registered_teams ORDER BY teamname ASC"))
    test = cur.fetchall()
    for member in test:
        mem1 = ctx.guild.get_member(int(member[0]))
        cur.execute(sql.SQL("SELECT userign FROM registered_users WHERE discordid=%s"), [str(mem1)])
        memb1 = cur.fetchone()
        mem2 = ctx.guild.get_member(int(member[1]))
        cur.execute(sql.SQL("SELECT userign FROM registered_users WHERE discordid=%s"), [str(mem2)])
        memb2 = cur.fetchone()
        mem3 = ctx.guild.get_member(int(member[2]))
        cur.execute(sql.SQL("SELECT userign FROM registered_users WHERE discordid=%s"), [str(mem3)])
        memb3 = cur.fetchone()
        strng = member[3] + " :  " + str(memb1)[2:-3] + "   " + str(memb2)[2:-3] + "   " + str(memb3)[2:-3]
        await ctx.send(strng)

@bot.command(name='groups', help='print the team names in each group')
async def groups(ctx):
    print(ctx)
    cur.execute(sql.SQL("SELECT teamid FROM signup where seed ='Group A'"))
    groupa = cur.fetchall()
    await ctx.send("Group A: ")
    for teams in groupa:
        cur.execute(sql.SQL("SELECT teamname FROM registered_teams where teamid = %s"), [teams[0]])
        nam = cur.fetchone()
        await ctx.send(nam[0])
    cur.execute(sql.SQL("SELECT teamid FROM signup where seed ='Group B'"))
    groupb = cur.fetchall()
    await ctx.send("Group B: ")
    for teams in groupb:
        cur.execute(sql.SQL("SELECT teamname FROM registered_teams where teamid = %s"), [teams[0]])
        nam = cur.fetchone()
        await ctx.send(nam[0])

@bot.command(name='spectator', help='Give yourself a spectator role')
async def spectator(ctx):
    member = ctx.author
    role = discord.utils.get(member.guild.roles, name="Spectator")
    await member.add_roles(role)
    await ctx.message.delete()


@bot.command(name='getid', help='get the id of mentioned user')
async def getid(ctx, mem):
    print(mem)

@bot.command(name='sync', help='sync the db')
async def sync(ctx):
    cur.execute(sql.SQL("SELECT player1, player2, player3 FROM registered_teams"))
    test = cur.fetchall()
    for members in test:
        for member in members:
            print(member)
            cur.execute(sql.SQL("SELECT teamid FROM registered_teams WHERE player1 = %s or player2 = %s or player3 = %s"), [member, member, member])
            teamid = cur.fetchone()
            print(teamid[0])
            user = ctx.guild.get_member(int(member))
            cur.execute(sql.SQL("UPDATE registered_users SET teamid = %s WHERE discordid = %s"), [teamid[0], str(user)])


@bot.command(name='seed', help='Seed a given number of groups')
async def seed(ctx, num: int):
    groups = ["Group A", "Group B", "Group C", "Group D"]
    print(ctx.guild)
    for i in range(num):
        cur.execute(sql.SQL("SELECT teamid FROM signup WHERE seed = %s"),[groups[i]])
        seeded = cur.fetchall()
        if len(seeded) < 6:
            cur.execute("SELECT teamid FROM signup WHERE seed IS NULL")
            seeded.append(cur.fetchmany(6-len(seeded)))
        print("Seeded teams", seeded)
        if len(seeded) > 0:
            for team in seeded:
                if len(team) < 1:
                    return
                print("TEAM BEING PRINTED", team)
                teamnum = team[0]
                print(teamnum, type(teamnum))
                cur.execute(sql.SQL("SELECT player1, player2, player3 FROM registered_teams WHERE teamid = %s"), [teamnum])
                members = cur.fetchone()
                for members in members:
                    mem = ctx.guild.get_member(int(members))
                    role = discord.utils.get(ctx.guild.roles, name=groups[i])
                    await mem.add_roles(role)
                cur.execute(sql.SQL("UPDATE signup SET seed = %s WHERE teamid = %s"), [groups[i], teamnum])

def sortFunc(e):
    return e[1]

@bot.command(name='display', help='print the score of a given gameid')
@commands.has_role('ADMIN')
async def display(ctx, gameid: int):
    scorematrix = scorer(gameid)
    teammatrix = ["", "", "", "", "", ""]
    toFind = get_game(gameid)
    toFind.sort(key=sortFunc) #this function will sort the players based on placement.
                                # since the scorematrix is also based on placement we just have to compare indices 1-to-1
                                # need to  query index 0, 3, 6, 9, 12, 15 with the 0th index to find that players teamid
    testval = 0
    for player in toFind[::3]:
        cur.execute(sql.SQL("SELECT teamid FROM registered_users WHERE userign = %s"), [player[0]])
        teamid = cur.fetchone()
        if teamid is not None:
            cur.execute(sql.SQL("SELECT teamname FROM registered_teams WHERE teamid = %s"), [teamid[0]])
            teamname = cur.fetchone()

            print("Teamname: ", teamname[0])
            teammatrix[testval] = teamname[0]
        testval += 1
    testVal = 0
    for vals in scorematrix:
        await ctx.send(" {} : {}".format(testVal, vals))
        print("{} : {}".format(teammatrix[testVal], vals))
        testVal += 1

@bot.command(name='score', help='print the score of a given gameid')
@commands.has_role('ADMIN')
async def score(ctx, gameid: int):
    scorematrix = scorer(gameid)
    teammatrix = ["", "", "", "", "", ""]
    teamids = [0, 0, 0, 0, 0, 0]
    toFind = get_game(gameid)
    toFind.sort(key=sortFunc) #this function will sort the players based on placement.
                                # since the scorematrix is also based on placement we just have to compare indices 1-to-1
                                # need to  query index 0, 3, 6, 9, 12, 15 with the 0th index to find that players teamid
    testval = 0
    for player in toFind[::3]:
        cur.execute(sql.SQL("SELECT teamid FROM registered_users WHERE userign = %s"), [player[0]])
        teamid = cur.fetchone()
        if teamid is not None:
            cur.execute(sql.SQL("SELECT teamname FROM registered_teams WHERE teamid = %s"), [teamid[0]])
            teamids[testval] = teamid[0]
            teamname = cur.fetchone()

            print("Teamname: ", teamname[0])
            teammatrix[testval] = teamname[0]
        testval += 1
    testVal = 0
    for vals in scorematrix:
        #await ctx.send(" {} : {}".format(testVal, vals))
        print("{} : {}".format(teammatrix[testVal], vals))
        testVal += 1
        cur.execute(sql.SQL("INSERT INTO temp_rankings (teamid, teamname, score) values %s, %s, %s"), [teamids[testVal], teammatrix[testVal] , vals])


@bot.command(name='set', help='close out a set')
@commands.has_role('ADMIN')
async def set(ctx):
    groupascores = [0,0,0,0,0,0]
    groupbscores = [0,0,0,0,0,0]
    grpa = []
    grpb = []
    a = []
    b = []


    cur.execute(sql.SQL("SELECT teamid, loss FROM signup WHERE seed='Group A'"))
    groupa = cur.fetchall()
    tempint = 0
    for group in groupa:
        cur.execute(sql.SQL("SELECT score FROM temp_rankings WHERE teamid=%s"), [group[0]])
        grpa.append(group[0])
        temp = cur.fetchall()
        for score in temp:
            groupascores[tempint] += score

    cur.execute(sql.SQL("SELECT teamid, loss FROM signup WHERE seed='Group B'"))
    groupb = cur.fetchall()
    tempint = 0
    for group in groupb:
        cur.execute(sql.SQL("SELECT score FROM temp_rankings WHERE teamid=%s"), [group[0]])
        grpa.append(group[0])
        temp = cur.fetchall()
        for score in temp:
            groupbscores[tempint] += score

    print("Group a scores: ", groupascores)
    print("Group a teams: ", grpa)
    print("Group b scores: ", groupbscores)
    print("Group b teams: ", grpb)
    for i in range(6):
        a.append([groupascores[i], grpa[i]])
        b.append([groupbscores[i], grpb[i]])

    a.sort(key=lambda x: x[1], reverse=True)
    b.sort(key=lambda x: x[1], reverse=True)
    print("a: ", b)
    print("a: ", a)

    for team in a[3:]:
        if team[1] is True:
            cur.execute(sql.SQL("UPDATE signup SET seed = 'Group C' WHERE teamid = %s"), [team[0]])
            #remove their group a role
        else:
            cur.execute(sql.SQL("UPDATE signup SET seed = 'Group B' WHERE teamid = %s"), [team[0]])
            cur.execute(sql.SQL("UPDATE signup SET loss = True WHERE teamid = %s"), [team[0]])
            #remove group a role
            #add group B role
    for team in b[3:]:
        if team[1] is True:
            cur.execute(sql.SQL("UPDATE signup SET seed = 'Group C' WHERE teamid = %s"), [team[0]])
            #remove their group B role
        else:
            cur.execute(sql.SQL("UPDATE signup SET loss = True WHERE teamid = %s"), [team[0]])
    for team in b[:2]:
        cur.execute(sql.SQL("UPDATE signup SET seed = 'Group A' WHERE teamid = %s"), [team[0]])
        #remove group B role
        #add group a role


@bot.command(name='final', help='finalize a week of games')
@commands.has_role('ADMIN')
async def final(ctx):
    totalscores = [0, 0, 0, 0, 0, 0]
    teamnames = []
    cur.execute(sql.SQL("SELECT teamid FROM signup where seed = 'Group A'"))
    temp = cur.fetchall()
    tempint = 0
    for team in temp:
        cur.execute(sql.SQL("SELECT score, teamname FROM temp_rankings where teamid = %s"), [team[0]])
        scores = cur.fetchall()
        for scor in scores:
            teamnames.append(scor[1])
            totalscores[tempint] += scor[0]


@bot.command(name='eval', help='print the score of a given gameid')
@commands.has_role('ADMIN')
async def eval(ctx, gameid: int):
    testVal = 1
    scorematrix = scorer(gameid)
    for vals in scorematrix:
        await ctx.send("Team {} points: {}".format(testVal, vals))
        testVal += 1

def scorer(gameid):
    toScore = get_game(gameid)
    toScore.sort(key=sortFunc)
    print(toScore)
    cur.execute("SELECT * FROM objective_points WHERE name = 'teamKill'")
    test = cur.fetchone()
    kill = test[1]
    cur.execute("SELECT * FROM objective_points WHERE name = 'Alpha'")
    test = cur.fetchone()
    alpha = test[1]
    cur.execute("SELECT * FROM objective_points WHERE name = 'Omega'")
    test = cur.fetchone()
    omega = test[1]
    cur.execute("SELECT * FROM objective_points WHERE name = 'Wick'")
    test = cur.fetchone()
    wick = test[1]
    print(kill, wick, alpha, omega)
    monsterkills = [[],[],[],[],[],[]]
    scorematrix = [0, 0, 0, 0, 0, 0]
    killmatrix = [0, 0, 0, 0, 0, 0]
    for player in toScore:
        print(player)
        killmatrix[player[1]-1] += player[3]*kill
        if '8' in player[2]:
            scorematrix[player[1]-1] += alpha
            monsterkills[player[1]-1].append('A')
        if '9' in player[2]:
            scorematrix[player[1]-1] += omega
            monsterkills[player[1] - 1].append('O')
        if '7' in player[2]:
            scorematrix[player[1]-1] += wick
            monsterkills[player[1] - 1].append('W')
    print(scorematrix)
    scorematrix[0] = scorematrix[0] + math.floor(killmatrix[0]*1.3) + 10
    scorematrix[1] = scorematrix[1] + math.floor(killmatrix[1]*1.2) + 10
    scorematrix[2] = scorematrix[2] + math.floor(killmatrix[2]*1.1) + 10
    scorematrix[3] = scorematrix[3] + killmatrix[3] + 5
    scorematrix[4] = scorematrix[4] + killmatrix[4] + 3
    scorematrix[5] = scorematrix[5] + killmatrix[5] + 3
    return scorematrix

@bot.command(name='names', help='print the score of a given gameid')
@commands.has_role('ADMIN')
async def names(ctx):
    cur.execute("SELECT teamid FROM signup")
    ids = cur.fetchall()
    for id in ids:
        cur.execute("SELECT teamname FROM registered_teams WHERE teamid = %s", [id[0]])
        name = cur.fetchone()
        cur.execute("UPDATE signup SET teamname = %s WHERE teamid = %s", [name[0], id[0]])

@bot.command(name='resync', help='print the score of a given gameid')
@commands.has_role('ADMIN')
async def resync(ctx, msgID):
    msg = await ctx.fetch_message(msgID)
    print(msg)

@bot.command(name='discordIDS', help='Give yourself a spectator role')
@commands.has_role('ADMIN')
async def ats(ctx):
    print(ctx)
    cur.execute(sql.SQL("SELECT player1, player2, player3, teamname FROM registered_teams ORDER BY teamname ASC"))
    test = cur.fetchall()
    for member in test:
        mem1 = ctx.guild.get_member(int(member[0]))
        cur.execute(sql.SQL("SELECT discordid FROM registered_users WHERE discordid=%s"), [str(mem1)])
        memb1 = cur.fetchone()
        mem2 = ctx.guild.get_member(int(member[1]))
        cur.execute(sql.SQL("SELECT discordid FROM registered_users WHERE discordid=%s"), [str(mem2)])
        memb2 = cur.fetchone()
        mem3 = ctx.guild.get_member(int(member[2]))
        cur.execute(sql.SQL("SELECT discordid FROM registered_users WHERE discordid=%s"), [str(mem3)])
        memb3 = cur.fetchone()
        strng = member[3] + " :  " + str(memb1)[2:-3] + "   " + str(memb2)[2:-3] + "   " + str(memb3)[2:-3]
        await ctx.send(strng)


bot.run(TOKEN)
