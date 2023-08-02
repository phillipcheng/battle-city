#!/usr/bin/python
# coding=utf-8

import os, pygame, time, random, uuid, sys

from castle import Castle
from enemy import Enemy
from globals import Globals
from joystick import joystick_handler
from label import Label
from level import Level
from timer import Timer
from player import Player
from tricks import Tricks


class Game():
    # direction constants
    (DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT) = range(4)

    TILE_SIZE = 16

    def __init__(self, globals):
        self.globals = globals
        # center window
        os.environ['SDL_VIDEO_WINDOW_POS'] = 'center'

        if self.globals.play_sounds:
            pygame.mixer.pre_init(44100, -16, 1, 512)

        pygame.init()

        # init joystick
        self.joycount = pygame.joystick.get_count()
        self.joysticks = []
        for i in range(self.joycount):
            self.joysticks.append(joystick_handler(i))

        pygame.display.set_caption("Battle City")

        size = width, height = 480, 416

        if "-f" in sys.argv[1:]:
            self.globals.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
        else:
            self.globals.screen = pygame.display.set_mode(size)

        self.clock = pygame.time.Clock()

        # load sprites (funky version)
        # sprites = pygame.transform.scale2x(pygame.image.load("images/sprites.gif"))
        # load sprites (pixely version)
        self.globals.sprites = pygame.transform.scale(pygame.image.load("images/sprites.gif"), [192, 224])
        # screen.set_colorkey((0,138,104))

        pygame.display.set_icon(self.globals.sprites.subsurface(0, 0, 13 * 2, 13 * 2))

        # load sounds
        if self.globals.play_sounds:
            pygame.mixer.init(44100, -16, 1, 512)

            self.globals.sounds["start"] = pygame.mixer.Sound("sounds/gamestart.ogg")
            self.globals.sounds["end"] = pygame.mixer.Sound("sounds/gameover.ogg")
            self.globals.sounds["score"] = pygame.mixer.Sound("sounds/score.ogg")
            self.globals.sounds["bg"] = pygame.mixer.Sound("sounds/background.ogg")
            self.globals.sounds["fire"] = pygame.mixer.Sound("sounds/fire.ogg")
            self.globals.sounds["bonus"] = pygame.mixer.Sound("sounds/bonus.ogg")
            self.globals.sounds["explosion"] = pygame.mixer.Sound("sounds/explosion.ogg")
            self.globals.sounds["brick"] = pygame.mixer.Sound("sounds/brick.ogg")
            self.globals.sounds["steel"] = pygame.mixer.Sound("sounds/steel.ogg")

        self.enemy_life_image = self.globals.sprites.subsurface(81 * 2, 57 * 2, 7 * 2, 7 * 2)
        self.player_life_image = self.globals.sprites.subsurface(89 * 2, 56 * 2, 7 * 2, 8 * 2)
        self.flag_image = self.globals.sprites.subsurface(64 * 2, 49 * 2, 16 * 2, 15 * 2)

        # this is used in intro screen
        self.player_image = pygame.transform.rotate(self.globals.sprites.subsurface(0, 0, 13 * 2, 13 * 2), 270)

        # if true, no new enemies will be spawn during this time
        self.timefreeze = False

        # load custom font
        self.font = pygame.font.Font("fonts/prstart.ttf", 16)

        # pre-render game over text
        self.im_game_over = pygame.Surface((64, 40))
        self.im_game_over.set_colorkey((0, 0, 0))
        self.im_game_over.blit(self.font.render("GAME", False, (127, 64, 64)), [0, 0])
        self.im_game_over.blit(self.font.render("OVER", False, (127, 64, 64)), [0, 20])
        self.game_over_y = 416 + 40

        # number of players. here is defined preselected menu value
        self.nr_of_players = 1

        del self.globals.players[:]
        del self.globals.bullets[:]
        del self.globals.enemies[:]
        del self.globals.bonuses[:]

    def triggerBonus(self, bonus, player):
        """ Execute bonus powers """

        if self.globals.play_sounds:
            self.globals.sounds["bonus"].play()

        player.trophies["bonus"] += 1
        player.score += 500

        if bonus.bonus == bonus.BONUS_GRENADE:
            for enemy in self.globals.enemies:
                enemy.explode()
        elif bonus.bonus == bonus.BONUS_HELMET:
            self.shieldPlayer(player, True, 10000)
        elif bonus.bonus == bonus.BONUS_SHOVEL:
            self.level.buildFortress(self.level.TILE_STEEL)
            self.globals.timer.add(10000, lambda: self.level.buildFortress(self.level.TILE_BRICK), 1)
        elif bonus.bonus == bonus.BONUS_STAR:
            player.superpowers += 1
            if player.superpowers == 2:
                player.max_active_bullets = 2
        elif bonus.bonus == bonus.BONUS_TANK:
            player.lives += 1
        elif bonus.bonus == bonus.BONUS_TIMER:
            self.toggleEnemyFreeze(True)
            self.globals.timer.add(10000, lambda: self.toggleEnemyFreeze(False), 1)
        self.globals.bonuses.remove(bonus)

        self.globals.labels.append(Label(bonus.rect.topleft, "500", 500, globals=self.globals))

    def shieldPlayer(self, player, shield=True, duration=None):
        """ Add/remove shield
		player: player (not enemy)
		shield: true/false
		duration: in ms. if none, do not remove shield automatically
		"""
        player.shielded = shield
        if shield:
            player.timer_uuid_shield = self.globals.timer.add(100, lambda: player.toggleShieldImage())
        else:
            self.globals.timer.destroy(player.timer_uuid_shield)

        if shield and duration != None:
            self.globals.timer.add(duration, lambda: self.shieldPlayer(player, False), 1)

    def spawnEnemy(self):
        """ Spawn new enemy if needed
		Only add enemy if:
			- there are at least one in queue
			- map capacity hasn't exceeded its quota
			- now isn't timefreeze
		"""

        if len(self.globals.enemies) >= self.level.max_active_enemies:
            return
        if len(self.level.enemies_left) < 1 or self.timefreeze:
            return
        enemy = Enemy(self.level, 1, globals=self.globals)
        self.globals.enemies.append(enemy)

    def respawnPlayer(self, player, clear_scores=False):
        """ Respawn player """
        player.reset()

        if clear_scores:
            player.trophies = {
                "bonus": 0, "enemy0": 0, "enemy1": 0, "enemy2": 0, "enemy3": 0
            }

        self.shieldPlayer(player, True, 4000)

    def gameOver(self):
        """ End game and return to menu """

        print("Game Over")
        if self.globals.play_sounds:
            for sound in self.globals.sounds:
                self.globals.sounds[sound].stop()
            self.globals.sounds["end"].play()

        self.game_over_y = 416 + 40

        self.game_over = True
        self.globals.timer.add(3000, lambda: self.showScores(), 1)

    def gameOverScreen(self):
        """ Show game over screen """

        # stop game main loop (if any)
        self.running = False

        self.globals.screen.fill([0, 0, 0])

        self.writeInBricks("game", [125, 140])
        self.writeInBricks("over", [125, 220])
        pygame.display.flip()

        while 1:
            time_passed = self.clock.tick(50)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.showMenu()
                        return

    def showMenu(self):
        """ Show game menu
		Redraw screen only when up or down key is pressed. When enter is pressed,
		exit from this screen and start the game with selected number of players
		"""

        # stop game main loop (if any)
        self.running = False

        # clear all timers
        del self.globals.timer.timers[:]

        # set current stage to 0
        self.stage = 1

        self.animateIntroScreen()

        main_loop = True
        while main_loop:
            time_passed = self.clock.tick(50)

            for event in pygame.event.get():

                for i in range(self.joycount):
                    joystick = self.joysticks[i]
                    joystick.translate_event()

                if event.type == pygame.QUIT:
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        quit()
                    elif event.key == pygame.K_UP:
                        if self.nr_of_players == 2:
                            self.nr_of_players = 1
                            self.drawIntroScreen()
                    elif event.key == pygame.K_DOWN:
                        if self.nr_of_players == 1:
                            self.nr_of_players = 2
                            self.drawIntroScreen()
                    elif event.key == pygame.K_SPACE:
                        main_loop = False

        del self.globals.players[:]
        self.nextLevel()

    def reloadPlayers(self):
        """ Init players
		If players already exist, just reset them
		"""

        if len(self.globals.players) == 0:
            # first player
            x = 8 * self.TILE_SIZE + (self.TILE_SIZE * 2 - 26) / 2
            y = 24 * self.TILE_SIZE + (self.TILE_SIZE * 2 - 26) / 2

            player = Player(
                self.level, 0, [x, y], self.DIR_UP, (0, 0, 13 * 2, 13 * 2), globals=self.globals
            )
            self.globals.players.append(player)

            # second player
            if self.nr_of_players == 2:
                x = 16 * self.TILE_SIZE + (self.TILE_SIZE * 2 - 26) / 2
                y = 24 * self.TILE_SIZE + (self.TILE_SIZE * 2 - 26) / 2
                player = Player(
                    self.level, 0, [x, y], self.DIR_UP, (16 * 2, 0, 13 * 2, 13 * 2), globals=self.globals
                )
                player.controls = [pygame.K_f, pygame.K_w, pygame.K_d, pygame.K_s, pygame.K_a,
                                   pygame.K_z, pygame.K_x, pygame.K_c, pygame.K_v]
                self.globals.players.append(player)

        for player in self.globals.players:
            player.level = self.level
            self.respawnPlayer(player, True)

    def showScores(self):
        """ Show level scores """

        # stop game main loop (if any)
        self.running = False

        # clear all timers
        del self.globals.timer.timers[:]

        if self.globals.play_sounds:
            for sound in self.globals.sounds:
                self.globals.sounds[sound].stop()

        hiscore = self.loadHiscore()

        # update hiscore if needed
        if self.globals.players[0].score > hiscore:
            hiscore = self.globals.players[0].score
            self.saveHiscore(hiscore)
        if self.nr_of_players == 2 and self.globals.players[1].score > hiscore:
            hiscore = self.globals.players[1].score
            self.saveHiscore(hiscore)

        img_tanks = [
            self.globals.sprites.subsurface(32 * 2, 0, 13 * 2, 15 * 2),
            self.globals.sprites.subsurface(48 * 2, 0, 13 * 2, 15 * 2),
            self.globals.sprites.subsurface(64 * 2, 0, 13 * 2, 15 * 2),
            self.globals.sprites.subsurface(80 * 2, 0, 13 * 2, 15 * 2)
        ]

        img_arrows = [
            self.globals.sprites.subsurface(81 * 2, 48 * 2, 7 * 2, 7 * 2),
            self.globals.sprites.subsurface(88 * 2, 48 * 2, 7 * 2, 7 * 2)
        ]

        self.globals.screen.fill([0, 0, 0])

        # colors
        black = pygame.Color("black")
        white = pygame.Color("white")
        purple = pygame.Color(127, 64, 64)
        pink = pygame.Color(191, 160, 128)

        self.globals.screen.blit(self.font.render("HI-SCORE", False, purple), [105, 35])
        self.globals.screen.blit(self.font.render(str(hiscore), False, pink), [295, 35])

        self.globals.screen.blit(self.font.render("STAGE" + str(self.stage).rjust(3), False, white), [170, 65])

        self.globals.screen.blit(self.font.render("I-PLAYER", False, purple), [25, 95])

        # player 1 global score
        self.globals.screen.blit(self.font.render(str(self.globals.players[0].score).rjust(8), False, pink), [25, 125])

        if self.nr_of_players == 2:
            self.globals.screen.blit(self.font.render("II-PLAYER", False, purple), [310, 95])

            # player 2 global score
            self.globals.screen.blit(self.font.render(str(self.globals.players[1].score).rjust(8), False, pink),
                                     [325, 125])

        # tanks and arrows
        for i in range(4):
            self.globals.screen.blit(img_tanks[i], [226, 160 + (i * 45)])
            self.globals.screen.blit(img_arrows[0], [206, 168 + (i * 45)])
            if self.nr_of_players == 2:
                self.globals.screen.blit(img_arrows[1], [258, 168 + (i * 45)])

        self.globals.screen.blit(self.font.render("TOTAL", False, white), [70, 335])

        # total underline
        pygame.draw.line(self.globals.screen, white, [170, 330], [307, 330], 4)

        pygame.display.flip()

        self.clock.tick(2)

        interval = 5

        # points and kills
        for i in range(4):

            # total specific tanks
            tanks = self.globals.players[0].trophies["enemy" + str(i)]

            for n in range(tanks + 1):
                if n > 0 and self.globals.play_sounds:
                    self.globals.sounds["score"].play()

                # erase previous text
                self.globals.screen.blit(self.font.render(str(n - 1).rjust(2), False, black), [170, 168 + (i * 45)])
                # print new number of enemies
                self.globals.screen.blit(self.font.render(str(n).rjust(2), False, white), [170, 168 + (i * 45)])
                # erase previous text
                self.globals.screen.blit(self.font.render(str((n - 1) * (i + 1) * 100).rjust(4) + " PTS", False, black),
                                         [25, 168 + (i * 45)])
                # print new total points per enemy
                self.globals.screen.blit(self.font.render(str(n * (i + 1) * 100).rjust(4) + " PTS", False, white),
                                         [25, 168 + (i * 45)])
                pygame.display.flip()
                self.clock.tick(interval)

            if self.nr_of_players == 2:
                tanks = self.globals.players[1].trophies["enemy" + str(i)]

                for n in range(tanks + 1):

                    if n > 0 and self.globals.play_sounds:
                        self.globals.sounds["score"].play()

                    self.globals.screen.blit(self.font.render(str(n - 1).rjust(2), False, black), [277, 168 + (i * 45)])
                    self.globals.screen.blit(self.font.render(str(n).rjust(2), False, white), [277, 168 + (i * 45)])

                    self.globals.screen.blit(
                        self.font.render(str((n - 1) * (i + 1) * 100).rjust(4) + " PTS", False, black),
                        [325, 168 + (i * 45)])
                    self.globals.screen.blit(self.font.render(str(n * (i + 1) * 100).rjust(4) + " PTS", False, white),
                                             [325, 168 + (i * 45)])

                    pygame.display.flip()
                    self.clock.tick(interval)

            self.clock.tick(interval)

        # total tanks
        tanks = sum([i for i in self.globals.players[0].trophies.values()]) - self.globals.players[0].trophies["bonus"]
        self.globals.screen.blit(self.font.render(str(tanks).rjust(2), False, white), [170, 335])
        if self.nr_of_players == 2:
            tanks = sum([i for i in self.globals.players[1].trophies.values()]) - self.globals.players[1].trophies[
                "bonus"]
            self.globals.screen.blit(self.font.render(str(tanks).rjust(2), False, white), [277, 335])

        pygame.display.flip()

        # do nothing for 2 seconds
        self.clock.tick(1)
        self.clock.tick(1)

        if self.game_over:
            self.gameOverScreen()
        else:
            self.nextLevel()

    def draw(self):

        self.globals.screen.fill([0, 0, 0])

        self.level.draw([self.level.TILE_EMPTY, self.level.TILE_BRICK, self.level.TILE_STEEL, self.level.TILE_FROZE,
                         self.level.TILE_WATER])

        self.globals.castle.draw()

        for enemy in self.globals.enemies:
            enemy.draw()

        for label in self.globals.labels:
            label.draw()

        for player in self.globals.players:
            player.draw()

        for bullet in self.globals.bullets:
            bullet.draw()

        for bonus in self.globals.bonuses:
            bonus.draw()

        self.level.draw([self.level.TILE_GRASS])

        if self.game_over:
            if self.game_over_y > 188:
                self.game_over_y -= 4
            self.globals.screen.blit(self.im_game_over, [176, self.game_over_y])  # 176=(416-64)/2

        self.drawSidebar()

        pygame.display.flip()

    def drawSidebar(self):

        x = 416
        y = 0
        self.globals.screen.fill([100, 100, 100], pygame.Rect([416, 0], [64, 416]))

        xpos = x + 16
        ypos = y + 16

        # draw enemy lives
        for n in range(len(self.level.enemies_left) + len(self.globals.enemies)):
            self.globals.screen.blit(self.enemy_life_image, [xpos, ypos])
            if n % 2 == 1:
                xpos = x + 16
                ypos += 17
            else:
                xpos += 17

        # players' lives
        if pygame.font.get_init():
            text_color = pygame.Color('black')
            for n in range(len(self.globals.players)):
                if n == 0:
                    self.globals.screen.blit(self.font.render(str(n + 1) + "P", False, text_color), [x + 16, y + 200])
                    self.globals.screen.blit(self.font.render(str(self.globals.players[n].lives), False, text_color),
                                             [x + 31, y + 215])
                    self.globals.screen.blit(self.player_life_image, [x + 17, y + 215])
                else:
                    self.globals.screen.blit(self.font.render(str(n + 1) + "P", False, text_color), [x + 16, y + 240])
                    self.globals.screen.blit(self.font.render(str(self.globals.players[n].lives), False, text_color),
                                             [x + 31, y + 255])
                    self.globals.screen.blit(self.player_life_image, [x + 17, y + 255])

            self.globals.screen.blit(self.flag_image, [x + 17, y + 280])
            self.globals.screen.blit(self.font.render(str(self.stage), False, text_color), [x + 17, y + 312])

    def drawIntroScreen(self, put_on_surface=True):
        """ Draw intro (menu) screen
		@param boolean put_on_surface If True, flip display after drawing
		@return None
		"""

        self.globals.screen.fill([0, 0, 0])

        if pygame.font.get_init():
            hiscore = self.loadHiscore()

            self.globals.screen.blit(self.font.render("HI- " + str(hiscore), True, pygame.Color('white')), [170, 35])

            self.globals.screen.blit(self.font.render("1 PLAYER", True, pygame.Color('white')), [165, 250])
            self.globals.screen.blit(self.font.render("2 PLAYERS", True, pygame.Color('white')), [165, 275])

            self.globals.screen.blit(self.font.render("(c) 1980 1985 NAMCO LTD.", True, pygame.Color('white')),
                                     [50, 350])
            self.globals.screen.blit(self.font.render("ALL RIGHTS RESERVED", True, pygame.Color('white')), [85, 380])

        if self.nr_of_players == 1:
            self.globals.screen.blit(self.player_image, [125, 245])
        elif self.nr_of_players == 2:
            self.globals.screen.blit(self.player_image, [125, 270])

        self.writeInBricks("battle", [65, 80])
        self.writeInBricks("city", [129, 160])

        if put_on_surface:
            pygame.display.flip()

    def animateIntroScreen(self):
        """ Slide intro (menu) screen from bottom to top
		If Enter key is pressed, finish animation immediately
		@return None
		"""

        self.drawIntroScreen(False)
        screen_cp = self.globals.screen.copy()

        self.globals.screen.fill([0, 0, 0])

        y = 416
        while (y > 0):
            time_passed = self.clock.tick(50)
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        y = 0
                        break

            self.globals.screen.blit(screen_cp, [0, y])
            pygame.display.flip()
            y -= 5

        self.globals.screen.blit(screen_cp, [0, 0])
        pygame.display.flip()

    def chunks(self, l, n):
        """ Split text string in chunks of specified size
		@param string l Input string
		@param int n Size (number of characters) of each chunk
		@return list
		"""
        return [l[i:i + n] for i in range(0, len(l), n)]

    def writeInBricks(self, text, pos):
        """ Write specified text in "brick font"
		Only those letters are available that form words "Battle City" and "Game Over"
		Both lowercase and uppercase are valid input, but output is always uppercase
		Each letter consists of 7x7 bricks which is converted into 49 character long string
		of 1's and 0's which in turn is then converted into hex to save some bytes
		@return None
		"""

        bricks = self.globals.sprites.subsurface(56 * 2, 64 * 2, 8 * 2, 8 * 2)
        brick1 = bricks.subsurface((0, 0, 8, 8))
        brick2 = bricks.subsurface((8, 0, 8, 8))
        brick3 = bricks.subsurface((8, 8, 8, 8))
        brick4 = bricks.subsurface((0, 8, 8, 8))

        alphabet = {
            "a": "0071b63c7ff1e3",
            "b": "01fb1e3fd8f1fe",
            "c": "00799e0c18199e",
            "e": "01fb060f98307e",
            "g": "007d860cf8d99f",
            "i": "01f8c183060c7e",
            "l": "0183060c18307e",
            "m": "018fbffffaf1e3",
            "o": "00fb1e3c78f1be",
            "r": "01fb1e3cff3767",
            "t": "01f8c183060c18",
            "v": "018f1e3eef8e08",
            "y": "019b3667860c18"
        }

        abs_x, abs_y = pos

        for letter in text.lower():

            binstr = ""
            for h in self.chunks(alphabet[letter], 2):
                binstr += str(bin(int(h, 16)))[2:].rjust(8, "0")
            binstr = binstr[7:]

            x, y = 0, 0
            letter_w = 0
            surf_letter = pygame.Surface((56, 56))
            for j, row in enumerate(self.chunks(binstr, 7)):
                for i, bit in enumerate(row):
                    if bit == "1":
                        if i % 2 == 0 and j % 2 == 0:
                            surf_letter.blit(brick1, [x, y])
                        elif i % 2 == 1 and j % 2 == 0:
                            surf_letter.blit(brick2, [x, y])
                        elif i % 2 == 1 and j % 2 == 1:
                            surf_letter.blit(brick3, [x, y])
                        elif i % 2 == 0 and j % 2 == 1:
                            surf_letter.blit(brick4, [x, y])
                        if x > letter_w:
                            letter_w = x
                    x += 8
                x = 0
                y += 8
            self.globals.screen.blit(surf_letter, [abs_x, abs_y])
            abs_x += letter_w + 16

    def toggleEnemyFreeze(self, freeze=True):
        """ Freeze/defreeze all enemies """

        for enemy in self.globals.enemies:
            enemy.paused = freeze
        self.timefreeze = freeze

    def loadHiscore(self):
        """ Load hiscore
		Really primitive version =] If for some reason hiscore cannot be loaded, return 20000
		@return int
		"""
        filename = ".hiscore"
        if (not os.path.isfile(filename)):
            return 20000

        f = open(filename, "r")
        hiscore = int(f.read())

        if hiscore > 19999 and hiscore < 1000000:
            return hiscore
        else:
            print("cheater =[")
            return 20000

    def saveHiscore(self, hiscore):
        """ Save hiscore
		@return boolean
		"""
        try:
            f = open(".hiscore", "w")
        except:
            print("Can't save hi-score")
            return False
        f.write(str(hiscore))
        f.close()
        return True

    def finishLevel(self):
        """ Finish current level
		Show earned scores and advance to the next stage
		"""

        if self.globals.play_sounds:
            self.globals.sounds["bg"].stop()

        self.active = False
        self.globals.timer.add(3000, lambda: self.showScores(), 1)

        print("Stage " + str(self.stage) + " completed")

    def nextLevel(self):
        """ Start next level """

        del self.globals.bullets[:]
        del self.globals.enemies[:]
        del self.globals.bonuses[:]
        self.globals.castle.rebuild()
        del self.globals.timer.timers[:]

        # load level
        self.stage += 1
        self.level = Level(self.stage, self.globals)
        self.timefreeze = False

        # set number of enemies by types (basic, fast, power, armor) according to level
        levels_enemies = (
            (18, 2, 0, 0), (14, 4, 0, 2), (14, 4, 0, 2), (2, 5, 10, 3), (8, 5, 5, 2),
            (9, 2, 7, 2), (7, 4, 6, 3), (7, 4, 7, 2), (6, 4, 7, 3), (12, 2, 4, 2),
            (5, 5, 4, 6), (0, 6, 8, 6), (0, 8, 8, 4), (0, 4, 10, 6), (0, 2, 10, 8),
            (16, 2, 0, 2), (8, 2, 8, 2), (2, 8, 6, 4), (4, 4, 4, 8), (2, 8, 2, 8),
            (6, 2, 8, 4), (6, 8, 2, 4), (0, 10, 4, 6), (10, 4, 4, 2), (0, 8, 2, 10),
            (4, 6, 4, 6), (2, 8, 2, 8), (15, 2, 2, 1), (0, 4, 10, 6), (4, 8, 4, 4),
            (3, 8, 3, 6), (6, 4, 2, 8), (4, 4, 4, 8), (0, 10, 4, 6), (0, 6, 4, 10)
        )

        if self.stage <= 35:
            enemies_l = levels_enemies[self.stage - 1]
        else:
            enemies_l = levels_enemies[34]

        self.level.enemies_left = [0] * enemies_l[0] + [1] * enemies_l[1] + [2] * enemies_l[2] + [3] * enemies_l[3]
        random.shuffle(self.level.enemies_left)

        if self.globals.play_sounds:
            self.globals.sounds["start"].play()
            self.globals.timer.add(4330, lambda: self.globals.sounds["bg"].play(-1), 1)

        self.reloadPlayers()

        self.globals.timer.add(3000, lambda: self.spawnEnemy())

        # if True, start "game over" animation
        self.game_over = False

        # if False, game will end w/o "game over" bussiness
        self.running = True

        # if False, players won't be able to do anything
        self.active = True

        self.draw()

        while self.running:

            time_passed = self.clock.tick(50)

            for i in range(self.joycount):
                joystick = self.joysticks[i]
                joystick.translate_event()

            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pass
                elif event.type == pygame.QUIT:
                    quit()
                elif event.type == pygame.KEYDOWN and not self.game_over and self.active:

                    if event.key == pygame.K_q:
                        quit()
                    # toggle sounds
                    elif event.key == pygame.K_m:
                        self.globals.play_sounds = not self.globals.play_sounds
                        if not self.globals.play_sounds:
                            pygame.mixer.stop()
                        else:
                            self.globals.sounds["bg"].play(-1)

                    for player in self.globals.players:
                        if player.state == player.STATE_ALIVE:
                            try:
                                index = player.controls.index(event.key)
                            except:
                                pass
                            else:
                                if index == 0:
                                    if player.fire() and self.globals.play_sounds:
                                        self.globals.sounds["fire"].play()
                                elif index == 1:
                                    player.pressed[0] = True
                                elif index == 2:
                                    player.pressed[1] = True
                                elif index == 3:
                                    player.pressed[2] = True
                                elif index == 4:
                                    player.pressed[3] = True
                                elif index == 5:
                                    if self.globals.tricks is not None and self.globals.tricks.helmet_me:
                                        self.shieldPlayer(player, shield=True, duration=10000)
                                elif index == 6:
                                    if self.globals.tricks is not None and self.globals.tricks.freeze_enemy:
                                        self.toggleEnemyFreeze(True)
                                        self.globals.timer.add(10000, lambda: self.toggleEnemyFreeze(False), 1)
                                elif index == 7:
                                    if self.globals.tricks is not None and self.globals.tricks.fire_all:
                                        if player.fire(allow_full_fire=True, all_direction=True) and self.globals.play_sounds:
                                            self.globals.sounds["fire"].play()
                                elif index == 8:
                                    if self.globals.tricks is None:
                                        self.globals.tricks = Tricks()
                                        self.globals.castle.tricks = self.globals.tricks
                                        for player in self.globals.players:
                                            player.globals.tricks = self.globals.tricks
                                            player.superpowers = self.globals.tricks.player_bullet_super_power
                                            player.speed = self.globals.tricks.player_bullet_speed
                                    else:
                                        self.globals.tricks = None
                                        self.globals.castle.tricks = None
                                        for player in self.globals.players:
                                            player.globals.tricks = None
                elif event.type == pygame.KEYUP and not self.game_over and self.active:
                    for player in self.globals.players:
                        if player.state == player.STATE_ALIVE:
                            try:
                                index = player.controls.index(event.key)
                            except:
                                pass
                            else:
                                if index == 1:
                                    player.pressed[0] = False
                                elif index == 2:
                                    player.pressed[1] = False
                                elif index == 3:
                                    player.pressed[2] = False
                                elif index == 4:
                                    player.pressed[3] = False

            for player in self.globals.players:
                if player.state == player.STATE_ALIVE and not self.game_over and self.active:
                    if player.pressed[0] == True:
                        player.move(self.DIR_UP);
                    elif player.pressed[1] == True:
                        player.move(self.DIR_RIGHT);
                    elif player.pressed[2] == True:
                        player.move(self.DIR_DOWN);
                    elif player.pressed[3] == True:
                        player.move(self.DIR_LEFT);
                player.update(time_passed)

            for enemy in self.globals.enemies:
                if enemy.state == enemy.STATE_DEAD and not self.game_over and self.active:
                    self.globals.enemies.remove(enemy)
                    if len(self.level.enemies_left) == 0 and len(self.globals.enemies) == 0:
                        self.finishLevel()
                else:
                    enemy.update(time_passed)

            if not self.game_over and self.active:
                for player in self.globals.players:
                    if player.state == player.STATE_ALIVE:
                        if player.bonus != None and player.side == player.SIDE_PLAYER:
                            self.triggerBonus(bonus, player)
                            player.bonus = None
                    elif player.state == player.STATE_DEAD:
                        self.superpowers = 0
                        player.lives -= 1
                        if player.lives > 0:
                            self.respawnPlayer(player)
                        else:
                            self.gameOver()

            for bullet in self.globals.bullets:
                if bullet.state == bullet.STATE_REMOVED:
                    self.globals.bullets.remove(bullet)
                else:
                    bullet.update()

            for bonus in self.globals.bonuses:
                if bonus.active == False:
                    self.globals.bonuses.remove(bonus)

            for label in self.globals.labels:
                if not label.active:
                    self.globals.labels.remove(label)

            if not self.game_over:
                if not self.globals.castle.active:
                    self.gameOver()

            self.globals.timer.update(time_passed)

            self.draw()
