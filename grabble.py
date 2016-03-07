# This is a class to play Grabble.

# Written for an IRC bot, so there are a few assumptions:
#
# * Assumption 1: Players are identified uniquely by name, and can join at any
#   time
# * Assumption 2: English Scrabble tiles

import random

class Grabble:
    class NotYourGoError:
        pass
    class NotAWordError:
        pass
    class NotFoundError:
        pass

    def __init__(self):
        self.tiles = [" "] * 2 + ["E"] * 12 + ["A"] * 9 + ["I"] * 9 \
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
            raise NotYourGoError
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
        if not player in self.turn_order:
            pass
        if self.current_turn == name:
            self.current_turn = self.turn_order[(self.turn_order.index(name)
                + 1) % len(self.turn_order)]
        self.turn_order.remove(name)

    def is_word(self, word):
        return True

    def is_complete_anagram(self, word1, word2):
        return sorted(word1) == sorted(word2)

    def is_subanagram(self, word1, word2):
        sorted_old_word_dup = sorted(word2)
        sorted_word_dup = sorted(word1)
        for i in sorted_old_word_dup:
            if not i in sorted_word_dup:
                return False
            sorted_word_dup.remove(i)
        return True

    def find_subanagrams(self, word, so_far = []):
        if len(word) >= 3:
            for old_name, the_words in self.words:
                for old_word in [x for x in words if len(x.name) <= len(word)]:
                    if old_word in so_far:
                        continue
                    if self.is_complete_anagram(word, old_word.name):
                        return (so_far + [old_word], [])
                    if not self.is_subanagram(word, old_word.name):
                        continue
                    missing_letters = ''.join([x for x in sorted(word)
                        if x not in sorted(old_word.name)])
                    return self.find_subanagrams(missing_letters, so_far)
        return self.scan_tiles(word, so_far)

    def scan_words(self, name, word, name_equal):
        for old_name, words in self.words:
            if (old_name == name) == name_equal:
                for old_word in [x for x in words if len(x.name) <= len(word)]:
                    if word in old_word.prev or (word[-1] == "s" and \
                            word[:-1] in old_word.prev):
                        continue
                    words_used = [old_word]
                    if self.is_complete_anagram(word, old_word.name):
                        return (words_used, [])
                    # Now check that the anagram makes sense
                    if not self.is_subanagram(word, old_word.name):
                        continue
                    # so not a perfect anagram, but is a subset
                    # now we need to find other words to add that will make
                    # up the difference
                    
                    # so, let's try a different tactic — produce the letters
                    # that we want, and search for words that contain no more
                    # than them
                    missing_letters = ''.join([x for x in sorted(word)
                        if x not in sorted(old_word.name)])
                    return self.find_subanagrams(missing_letters, words_used)

    def scan_tiles(self, name, word, so_far = []):
        if self.is_subanagram(word, ''.join(self.flipped_tiles)):
            return ([], sorted(word))
        return ([], [])

    def suggest_word(self, name, word):
        # First, add them to the turn rotor if they don't exist.
        if not name in self.turn_order:
            if self.current_turn is None:
                self.turn_order += [name]
            else:
                self.turn_order.insert(self.turn_order.index(
                    self.current_turn), name)

        if not self.is_word(word):
            raise NotAWordError

        # We have to try to figure out which word they want to change.
        # First, scan opponents' words.
        old_words, tiles = self.scan_words(name, word, name_equal=False)
        if not old_words:
            # Then, scan own words.
            old_words, tiles = self.scan_words(name, word, name_equal=True)
            if not old_words:
                # Finally, scan just tiles.
                old_words, tiles = self.scan_tiles(name, word)

        # Check if they're correct
        if not old_words and not tiles:
            raise NotFoundError
        # If so, make it their go and do other admin stuff
        self.current_turn = name
        for old_word in old_words:
            self.words[old_word.player].remove(old_word)
        for tile in tiles:
            self.flipped_tiles.remove(tile)
        old_word.player = name
        old_word.prev_words += [old_word.name]
        old_word.name = word
        if name in self.words:
            self.words[name] += [old_word]
        else:
            self.words[name] = [old_word]
