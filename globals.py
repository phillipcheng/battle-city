from castle import Castle
from timer import Timer
from tricks import Tricks


class Globals():
    def __init__(self, tricks: Tricks, timer:Timer, sprites, screen, players, enemies, bullets, bonuses, labels, castle:Castle, play_sounds:bool, sounds):
        self.tricks = tricks
        self.timer = timer

        self.sprites = sprites
        self.screen = screen
        self.players = players
        self.enemies = enemies
        self.bullets = bullets
        self.bonuses = bonuses
        self.labels = labels
        self.castle = castle

        self.play_sounds = play_sounds
        self.sounds = sounds
