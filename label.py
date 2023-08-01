import pygame


class Label():
	def __init__(self, position, text = "", duration = None, globals = None):

		self.globals = globals

		self.position = position

		self.active = True

		self.text = text

		self.font = pygame.font.SysFont("Arial", 13)

		if duration != None:
			self.globals.timer.add(duration, lambda :self.destroy(), 1)

	def draw(self):
		""" draw label """
		self.globals.screen.blit(self.font.render(self.text, False, (200,200,200)), [self.position[0]+4, self.position[1]+8])

	def destroy(self):
		self.active = False
