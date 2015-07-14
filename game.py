#! usr/bin/env python

import csv
import time
import json
import sys
import random

TEXT_SPEED = 1
STARTING_SCENE = 'start1'
HELP_TEXT = """Available Commands:
-------------------
look: Looks around you.
take [item]: Tries to take item from area.
go [direction]: Takes you 'north', 'south', 'east', or 'west'.
inventory: Looks at the items in your backpack.
quit: Exits out of the game.
help: Prints this message.
"""

try:
    input = raw_input
except NameError:
    pass


def spaced_print(text):
    texts = text.split("\n")
    for t in texts:
        print t
        time.sleep(TEXT_SPEED)


class Game:
    def __init__(self):
        self.is_playing = True
        self.turn = 0
        self.inventory = []
        with open("events.json") as scene_data:
            self.scenes = json.load(scene_data)['events']

    def quit(self, is_victory=False):
        if is_victory:
            spaced_print("\nYou won!")
        spaced_print("\nThanks for playing!")
        sys.exit()

    def load_scene(self, scene_name):
        for s in self.scenes:
            if s.get('name') == scene_name:
                self.current_scene = Room(s, self)
                return True
        return False

    def start_game(self):
        spaced_print("Welcome to 'The Map: The Video Game'!\nGame starting\n.\n..\n...\nNow!")
        success = self.load_scene(STARTING_SCENE)

        if not success:
            self.is_playing = False
            print("Whoops, there has been a developer error.")

    def restart_game(self):
        with open("events.json") as scene_data:
            self.scenes = json.load(scene_data)['events']

        self.inventory = []
        self.load_scene(STARTING_SCENE)
        return self

    def process_turn(self):
        self.turn += 1
        self.current_scene.run_scene()


class Room:
    def __init__(self, data, game):
        self.data = data
        self.game = game

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = value

    def death_message(self):
        spaced_print(self.get('death_message'))
        spaced_print('and the world fades to black...\n\n')
        self.game = self.game.restart_game()
        time.sleep(TEXT_SPEED)
        return

    def run_scene(self):
        if (self.get('visited') and self.get('visited_message')):
            spaced_print(self.get('visited_message'))
        else:
            spaced_print(self.get('intro_message'))

        if (not self.get('visited') and self.get('choices')):
            idx = 1
            for c in self.get('choices'):
                if (not c.get('required') or (c.get('required') and
                                              c.get('required') in self.game.inventory)):
                    print('{}) {}'.format(str(idx), c.get('choice')))
                    idx += 1

            self.make_choice()

        if (self.get('is_death')):
            if (self.get("required_to_live") and not self.get('visited')):
                for item in (self.get("required_to_live")):
                    if item.get('item') in self.game.inventory:
                        self.game.inventory.remove(item.get('item'))
                        spaced_print(item.get('message'))
                    else:
                        self.death_message()
                        self.game.load_scene(STARTING_SCENE)
                        return
            elif (self.get("required_to_die")):
                for item in (self.get("required_to_die")):
                    if item.get('item') in self.game.inventory:
                        self.death_message()
                        self.game.load_scene(STARTING_SCENE)
                        return
                    if item.get('item') not in self.game.inventory:
                        pass
            elif (self.get('visited')):
                pass
            else:
                self.death_message()
                self.game.load_scene(STARTING_SCENE)
                return

        if (self.get('is_victory')):
            spaced_print(self.get('victory_message'))
            self.game.quit(True)
            return

        if (self.get('go_to_random')):
            scene = random.choice(self.game.scenes)
            self.game.load_scene(scene.get('name'))
            return

        self.run_command()

        self.set('visited', True)

    def make_choice(self):
        try:
            choice = int(input('Which one do you choose? '))
        except ValueError:
            spaced_print(" \nThat is not a valid choice.")
            return self.make_choice()

        required_items = [c for c in self.get('choices') if
                          (not c.get('required') or c.get('required') in self.game.inventory)]
        if (choice <= len(required_items) and choice > 0):
            spaced_print(required_items[choice-1].get('message'))
            spaced_print(' ')
            if required_items[choice-1].get('item'):
                self.game.inventory.append(required_items[choice-1].get('item'))
            return True

        spaced_print(' \nThat is not a valid choice.')
        return self.make_choice()

    def run_command(self):
        commands = input("What do you want to do? ").lower().split(' ')

        if commands[0] == "look":
            spaced_print(self.get('look_message'))

        elif commands[0] == "take":
            if len(commands) > 1:
                if self.get('obtainable_items'):
                    for item in (self.get('obtainable_items')):
                        if commands[1] == item.get('item').lower():
                            if not item.get('required') or (item.get('required') in
                                                            self.game.inventory):
                                self.game.inventory.append(item.get('item').lower())
                                spaced_print(item.get('message'))
                            else:
                                spaced_print('\nSeems you can\'t take {}\n'.format(commands[1]))
                elif self.get('unobtainable_items'):
                    for item in (self.get('unobtainable_items')):
                        if commands[1] == item.get('item').lower():
                            if not item.get('required') or (item.get('required') in
                                                            self.game.inventory):
                                spaced_print(item.get('message'))
                            else:
                                spaced_print('\n: {}\n'.format(commands[1]))
                else:
                    spaced_print('\nSeems you can\'t take {}\n'.format(commands[1]))
            else:
                spaced_print('\nYou didn\'t specify what you wanted to take.\n')

        elif commands[0] in ["go", "move", "walk", "travel", "run", "skip", "hop", "crawl", "jump"]:
            if len(commands) > 1:
                if commands[1] in ["north", "up"]:
                    if self.get('directions')[0]:
                        self.game.load_scene(self.get('directions')[0])
                        return
                    else:
                        spaced_print('Seems you cant go that way.')
                if commands[1] in ["east", "right"]:
                    if self.get('directions')[1]:
                        self.game.load_scene(self.get('directions')[1])
                        return
                    else:
                        spaced_print('Seems you cant go that way.')
                if commands[1] in ["south", "down"]:
                    if self.get('directions')[2]:
                        self.game.load_scene(self.get('directions')[2])
                        return
                    else:
                        spaced_print('Seems you cant go that way.')
                if commands[1] in ["west", "left"]:
                    if self.get('directions')[3]:
                        self.game.load_scene(self.get('directions')[3])
                        return
                    else:
                        spaced_print('Seems you cant go that way.')
            else:
                spaced_print('Where do you want to go?')

        elif commands[0] in ['inventory', 'inv', 'backpack']:
            print(' | '.join(self.game.inventory))

        elif commands[0] == "quit" or commands[0] == "exit":
            self.game.quit()

        elif commands[0] == "help":
            print(HELP_TEXT)

        else:
            spaced_print(" \nCommand '"+' '.join(commands)+"' not recognized.")
            spaced_print("Use 'help' command to see available commands to you.\n ")

        return self.run_command()

game = Game()
game.start_game()

try:
    while (game.is_playing):
        game.process_turn()
except KeyboardInterrupt:
    game.quit()
