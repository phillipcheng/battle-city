import pygame

from tank import Tank


class Player(Tank):

	def __init__(self, level, type, position = None, direction = None, filename = None, globals=None):
		if globals.tricks is not None:
			Tank.__init__(self, level, type, position = None, direction = None, filename = None, globals=globals, super_power=globals.tricks.player_bullet_super_power, speed_in=globals.tricks.player_bullet_speed)
		else:
			Tank.__init__(self, level, type, position=None, direction=None, filename=None, globals=globals)

		self.globals = globals

		if filename is None:
			filename = (0, 0, 16*2, 16*2)

		self.start_position = position
		self.start_direction = direction

		if globals.tricks is not None:
			self.lives = globals.tricks.player_lifes
		else:
			self.lives = 100

		# total score
		self.score = 0

		# store how many bonuses in this stage this player has collected
		self.trophies = {
			"bonus" : 0,
			"enemy0" : 0,
			"enemy1" : 0,
			"enemy2" : 0,
			"enemy3" : 0
		}

		self.image = self.globals.sprites.subsurface(filename)
		self.image_up = self.image;
		self.image_left = pygame.transform.rotate(self.image, 90)
		self.image_down = pygame.transform.rotate(self.image, 180)
		self.image_right = pygame.transform.rotate(self.image, 270)

		if direction == None:
			self.rotate(self.DIR_UP, False)
		else:
			self.rotate(direction, False)

	def move(self, direction):
		""" move player if possible """

		if self.state == self.STATE_EXPLODING:
			if not self.explosion.active:
				self.state = self.STATE_DEAD
				del self.explosion

		if self.state != self.STATE_ALIVE:
			return

		# rotate player
		if self.direction != direction:
			self.rotate(direction)

		if self.paralised:
			return

		# move player
		if direction == self.DIR_UP:
			new_position = [self.rect.left, self.rect.top - self.speed]
			if new_position[1] < 0:
				return
		elif direction == self.DIR_RIGHT:
			new_position = [self.rect.left + self.speed, self.rect.top]
			if new_position[0] > (416 - 26):
				return
		elif direction == self.DIR_DOWN:
			new_position = [self.rect.left, self.rect.top + self.speed]
			if new_position[1] > (416 - 26):
				return
		elif direction == self.DIR_LEFT:
			new_position = [self.rect.left - self.speed, self.rect.top]
			if new_position[0] < 0:
				return

		player_rect = pygame.Rect(new_position, [26, 26])

		# collisions with tiles
		if player_rect.collidelist(self.level.obstacle_rects) != -1:
			return

		# collisions with other players
		for player in self.globals.players:
			if player != self and player.state == player.STATE_ALIVE and player_rect.colliderect(player.rect) == True:
				return

		# collisions with enemies
		for enemy in self.globals.enemies:
			if player_rect.colliderect(enemy.rect) == True:
				return

		# collisions with bonuses
		for bonus in self.globals.bonuses:
			if player_rect.colliderect(bonus.rect) == True:
				self.bonus = bonus

		#if no collision, move player
		self.rect.topleft = (new_position[0], new_position[1])

	def reset(self):
		""" reset player """
		self.rotate(self.start_direction, False)
		self.rect.topleft = self.start_position
		if self.globals.tricks is not None:
			self.superpowers = self.globals.tricks.player_bullet_super_power
		else:
			self.superpowers = 0
		self.max_active_bullets = 1
		self.health = 100
		self.paralised = False
		self.paused = False
		self.pressed = [False] * 4
		self.state = self.STATE_ALIVE
