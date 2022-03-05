# Discord tournament bot  
This is just a bot I wrote to help organize an online tournament that some friends and I were hosting. The main goal of this bot is to allow users from different regions to sign up for a multi-elim tournament in teams of 3 where their scores were tracked week to week for an entire season. This isn't really a bot that can be used for another game, but I'll post it here anyway.

# Basic overview:
## Features:
  Allow users to link their ingame name to their discord id

  Automatically calculate the score of a game based on a custom algorithm using the gameid of the game

  Automatically give the correct discord roles to each user corresponding to their group

  Keep track of which users/teams belong in which group in a set

  Keep track of weekly and overall rankings

  Allow users to declare a static team that they will be participating with

  Allow users to sign their team up for events by simply reacting to a discord post

## Design:
 Bot was designed using discord.py and communicates with game API to get data from a specific match.
 
 Bot is connected to a postgres database which stores registered users, registered teams, overall scores of each team, and session scores for each team.

