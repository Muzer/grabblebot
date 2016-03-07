# This is a class to play Grabble.

# Written for an IRC bot, so there are a few assumptions:
#
# * Assumption 1: Players are identified uniquely by name, and can join at any
#   time
# * Assumption 2: English Scrabble tiles

import random

class Grabble:
    class NotYourGoError(Exception):
        pass
    class NotAWordError(Exception):
        pass
    class NotFoundError(Exception):
        pass
    class WordTooShortError(Exception):
        pass

    def __init__(self):
        self.tiles = ["@"] * 2 + ["E"] * 12 + ["A"] * 9 + ["I"] * 9 \
                   + ["O"] * 8 + ["N"] * 6 + ["R"] * 6 + ["T"] * 6 \
                   + ["L"] * 4 + ["S"] * 4 + ["U"] * 4 + ["D"] * 4 \
                   + ["G"] * 3 + ["B"] * 2 + ["C"] * 2 + ["M"] * 2 \
                   + ["P"] * 2 + ["F"] * 2 + ["H"] * 2 + ["V"] * 2 \
                   + ["W"] * 2 + ["Y"] * 2 + ["K", "J", "X", "Q", "Z"]
        # dict of lists of dicts containing things about each word.
        self.words = {}
        self.flipped_tiles = []
        self.turn_order = []
        self.current_turn = None

    def turn_over(self, name):
        if name in self.turn_order and self.current_turn != name:
            raise self.NotYourGoError
        if not name in self.turn_order:
            # A wild player appears!
            # See whose go it is, and add this person before them in the list
            if not self.current_turn is None:
                self.turn_order.insert(self.turn_order.index(
                    self.current_turn), name)
            else:
                self.turn_order += [name]

        # It's their turn, and the turn order mangling has been done. Now, flip
        # a tile
        tile = random.choice(self.tiles)
        self.flipped_tiles += tile
        self.tiles.remove(tile)
        self.current_turn = self.turn_order[(self.turn_order.index(name) + 1) %
                len(self.turn_order)]
        return tile

    def remove_player(self, name):
        if not name in self.turn_order:
            pass
        if self.current_turn == name:
            self.current_turn = self.turn_order[(self.turn_order.index(name)
                + 1) % len(self.turn_order)]
        self.turn_order.remove(name)
        if not self.turn_order:
            self.current_turn = None

    def is_word(self, word):
        return True

    def is_complete_anagram(self, word1, word2):
        return sorted(word1) == sorted(word2)

    def is_subanagram(self, word1, word2):
        sorted_old_word_dup = sorted(word2)
        sorted_word_dup = sorted(word1)
        for i in sorted_old_word_dup:
            if not i in sorted_word_dup:
                if not "@" in sorted_word_dup:
                    return (False, [])
                else:
                    sorted_word_dup.remove("@")
            else:
                sorted_word_dup.remove(i)
        return (True, sorted_word_dup)

    def find_subanagrams(self, word, so_far = []):
        if len(word) >= 3:
            for old_name, the_words in self.words.items():
                for old_word in [x for x in the_words if len(x["name"])
                        <= len(word)]:
                    if old_word in so_far:
                        continue
                    if self.is_complete_anagram(word, old_word["name"]):
                        return (so_far + [old_word], [])
                    subanagram, missing_letters = self.is_subanagram(word,
                            old_word["name"])
                    if not subanagram:
                        continue
                    return self.find_subanagrams(''.join(missing_letters),
                            so_far)
        print("Got here with " + word + " and " + str(so_far))
        return self.scan_tiles(word, so_far)

    def scan_words(self, name, word, name_equal):
        for old_name, words in self.words.items():
            if (old_name == name) == name_equal:
                for old_word in [x for x in words if len(x["name"])
                        <= len(word)]:
                    if word in old_word["prev"] or (word[-1] == "S" and \
                            word[:-1] in old_word["prev"]):
                        continue
                    words_used = [old_word]
                    if self.is_complete_anagram(word, old_word["name"]):
                        return (words_used, [])
                    print("Anagram")
                    # Now check that the anagram makes sense
                    subanagram, missing_letters = self.is_subanagram(word,
                            old_word["name"])
                    if not subanagram:
                        print("Not subanagram")
                        continue
                    # so not a perfect anagram, but is a subset
                    # now we need to find other words to add that will make
                    # up the difference
                    
                    # so, let's try a different tactic — produce the letters
                    # that we want, and search for words that contain no more
                    # than them
                    print("Subanagram")
                    return self.find_subanagrams(''.join(missing_letters),
                            words_used)
        return ([], [])

    def scan_tiles(self, word, so_far = []):
        if self.is_subanagram(''.join(self.flipped_tiles), word)[0]:
            return (so_far, sorted(word))
        return ([], [])

    def suggest_word(self, name, word):
        word = word.upper()
        if len(word) < 3:
            raise self.WordTooShortError
        # First, add them to the turn rotor if they don't exist.
        if not name in self.turn_order:
            if self.current_turn is None:
                self.turn_order += [name]
            else:
                self.turn_order.insert(self.turn_order.index(
                    self.current_turn), name)

        if not self.is_word(word):
            raise self.NotAWordError

        # We have to try to figure out which word they want to change.
        # First, scan opponents' words.
        print("Scanning opp words")
        old_words, tiles = self.scan_words(name, word, name_equal=False)
        if not old_words:
            # Then, scan own words.
            print("Scanning own words")
            old_words, tiles = self.scan_words(name, word, name_equal=True)
            if not old_words:
                # Finally, scan just tiles.
                print("Scanning tiles")
                old_words, tiles = self.scan_tiles(word)

        # Check if they're correct
        if not old_words and not tiles:
            raise self.NotFoundError
        # If so, make it their go and do other admin stuff
        self.current_turn = name
        for old_word in old_words:
            self.words[old_word["player"]].remove(old_word)
        for tile in tiles:
            if tile in self.flipped_tiles:
                self.flipped_tiles.remove(tile)
            else:
                self.flipped_tiles.remove("@")
        if old_words:
            old_word = old_words[0]
        else:
            old_word = {"prev": []}
        old_word["player"] = name
        old_word["prev"] += [word]
        old_word["name"] = word
        if name in self.words:
            self.words[name] += [old_word]
        else:
            self.words[name] = [old_word]
