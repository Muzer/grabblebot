#! /usr/bin/env python
import irc.bot
import irc.strings
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr

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
        string = "Flipped: " + ' '.join(self.instance.flipped_tiles) + " (" + \
                str(len(self.instance.tiles)) + " unrevealed tiles remaining)"
        self.msg(string)
        string = ""
        for user, words in self.instance.words.items():
            string += user + ': ' + ' '.join([x["name"] for x in words]) + "; "
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
                self.msg("Game in progress! Finish it first!")
        elif cmd == "\\turn":
            if self.instance:
                try:
                    self.instance.turn_over(nick)
                    self.print_shit()
                except grabble.Grabble.NotYourGoError:
                    self.msg("It's " + self.instance.current_turn +
                            "'s go, not yours!")
            else:
                self.msg("Game not started! Use \\\\start")
        else:
            if self.instance:
                try:
                    self.instance.suggest_word(nick, cmd)
                    self.msg(nick + " won " + cmd + "!")
                    self.print_shit()
                except grabble.Grabble.NotAWordError:
                    self.msg("That's not a word!")
                except grabble.Grabble.NotFoundError:
                    self.msg("That's not possible to make (or there's a bug)!")
                except grabble.Grabble.WordTooShortError:
                    self.msg("That word is too short. Three or more letters!")
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
