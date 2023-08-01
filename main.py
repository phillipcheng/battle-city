from castle import Castle
from game import Game
from globals import Globals
from timer import Timer

if __name__ == "__main__":
    gtimer = Timer()

    sprites = None
    screen = None
    players = []
    enemies = []
    bullets = []
    bonuses = []
    labels = []

    play_sounds = True
    sounds = {}


    globals = Globals(gtimer, sprites, screen, players, enemies, bullets, bonuses, labels, None, play_sounds, sounds)
    game = Game(globals)
    castle = Castle(gtimer, globals.screen, globals.sprites)
    globals.castle = castle
    game.showMenu()
