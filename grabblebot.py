#! /usr/bin/env python
import irc.bot
import irc.strings
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr
import re

import grabble

# Unicode magic
irc.client.ServerConnection.buffer_class = irc.buffer.LenientDecodingLineBuffer



class GrabbleBot(irc.bot.SingleServerIRCBot):
    instance = None
    def __init__(self, channel, nickname, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname,
                nickname)
        self.channel = channel

    def msg(self, message):
        c = self.connection
        i = 0
        sent = False
        while not sent:
            sent = True
            try:
                if i == 0:
                    c.privmsg(self.channel, message)
                else:
                    c.privmsg(self.channel, message[:i])
                    self.msg(message[i:])
            except irc.client.MessageTooLong:
                sent = False
                i -= 1

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)

    def on_privmsg(self, c, e):
        self.do_command(e, e.arguments[0])

    def on_pubmsg(self, c, e):
        a = e.arguments[0]
        if len(a) > 1 and a[0] == '\\':
            self.do_command(e, a[1:].strip())
        return

    def print_shit(self):
        string = "Flipped: \u0002" + ' '.join(self.instance.flipped_tiles) + \
                "\u0002 (" + str(len(self.instance.tiles)) + \
                " unrevealed tiles remaining)"
        self.msg(string)
        string = ""
        for user, words in self.instance.words.items():
            suser = re.sub(r'^(.)', '\\1\u200b', user)
            string += suser + ': \u0002' \
                    + ' '.join([x["name"] for x in words]) + "\u0002; "
        self.msg(string)
        self.msg("Current turn: " + self.instance.current_turn)

    def do_command(self, e, cmd):
        nick = e.source.nick
        c = self.connection

        if cmd == "\\leave":
            if self.instance:
                self.instance.remove_player(nick)
                self.msg("Player " + nick + " removed!")
            else:
                self.msg("Game not started! Use \\\\start")
        elif cmd == "\\start":
            if not self.instance:
                self.instance = grabble.Grabble()
                self.msg("New game started! Type \\\\turn to turn over a tile")
            else:
                self.msg("Game in progress! Finish it first with \\\\end!")
        elif cmd == "\\end":
            if self.instance:
                if self.instance.end(nick):
                    self.msg("Game ended!")
                    scorestr = "Final Scores: "
                    for user in self.instance.words:
                        scorestr += user + ": " + \
                                str(self.instance.score(user)) + "; "
                    self.msg(scorestr)
                    self.instance = None
                else:
                    self.msg(nick + " has requested game end. Waiting for all "
                            "players to concur. Type \\\\end if you haven't "
                            "already.")
            else:
                self.msg("Game already ended! Use \\\\start for a new one.")
        elif cmd == "\\turn" or cmd == "\\t":
            if self.instance:
                try:
                    self.instance.turn_over(nick)
                    self.print_shit()
                except grabble.Grabble.NotYourGoError:
                    self.msg("It's " + self.instance.current_turn +
                            "'s go, not yours!")
                except grabble.Grabble.NoTilesError:
                    self.msg("There are no tiles left! Type \\\\end if you "
                            "want it all to end.")
            else:
                self.msg("Game not started! Use \\\\start")
        elif cmd == "\\help" or cmd == "\\?":
            self.msg("Grabble is a word game that involves fast reactions and,"
                    " on a computer, fast typing! It is first and foremost a "
                    "real-life game, but this bot attempts to recreate it as "
                    "best as is possible on IRC. The rules of the game:")
            self.msg("People take it in turns to turn over face-down Scrabble™"
                    " tiles on a table. Anyone who sees a word in the face-up "
                    "tiles at any time may claim it, in which case they own "
                    "it. However, if anyone at any time spots an anagram of "
                    "any word someone owns, possibly combined with extra "
                    "face-up tiles or other existing words, they win it.")
            self.msg("There is a special rule: you cannot just add 'S' to the "
                    "end of a word which has already been made with that set "
                    "of tiles.")
            self.msg("Scoring: One point for first three letters of each word "
                    "at the end of the game; one point for each subsequent "
                    "letter.")
            self.msg("Commands recognised:")
            self.msg("\\<any word> — Claim word")
            self.msg("\\\\start — Start a new game of Grabble")
            self.msg("\\\\turn or \\\\t — Turn over a tile.")
            self.msg("\\\\leave — Leave a game. Please do this if you're "
                    "leaving IRC, else the game will halt without you!")
            self.msg("\\\\end — Express your desire to end the current game. "
                    "Everyone in the game must agree with you. Has the "
                    "side-effect of removing you from the turn order.")
            self.msg("\\\\help or \\\\? — This text")
        else:
            if self.instance:
                try:
                    self.instance.suggest_word(nick, cmd)
                    self.msg(nick + " won \u0002" + cmd + "\u0002!")
                    self.print_shit()
                except grabble.Grabble.NotAWordError:
                    self.msg(cmd + " is not a word!")
                except grabble.Grabble.NotFoundError:
                    self.msg(cmd + " is not possible to make!")
                except grabble.Grabble.WordTooShortError:
                    self.msg(cmd + " is too short. Three or more letters!")
            else:
                self.msg("Game not started! Use \\\\start")

def main():
    import sys
    if len(sys.argv) != 4:
        print("Usage: testbot <server[:port]> <channel> <nickname>")
        sys.exit(1)

    s = sys.argv[1].split(":", 1)
    server = s[0]
    if len(s) == 2:
        try:
            port = int(s[1])
        except ValueError:
            print("Error: Erroneous port.")
            sys.exit(1)
    else:
        port = 6667
    channel = sys.argv[2]
    nickname = sys.argv[3]

    bot = GrabbleBot(channel, nickname, server, port)
    bot.start()

if __name__ == "__main__":
    main()
