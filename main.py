from castle import Castle
from game import Game
from globals import Globals
from timer import Timer
from tricks import Tricks

if __name__ == "__main__":
    gtimer = Timer()
    # tricks = Tricks()
    tricks = None
    sprites = None
    screen = None
    players = []
    enemies = []
    bullets = []
    bonuses = []
    labels = []

    play_sounds = True
    sounds = {}

    globals = Globals(tricks, gtimer, sprites, screen, players, enemies, bullets, bonuses, labels, None, play_sounds, sounds)
    game = Game(globals)
    castle = Castle(gtimer, globals.screen, globals.sprites, tricks)
    globals.castle = castle
    game.showMenu()
