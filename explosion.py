

class Explosion():
	def __init__(self, position, timer, screen, sprites, interval = None, images = None):

		self.timer = timer
		self.screen = screen
		self.sprits = sprites
		self.position = [position[0]-16, position[1]-16]
		self.active = True

		if interval == None:
			interval = 100

		if images == None:
			images = [
				sprites.subsurface(0, 80*2, 32*2, 32*2),
				sprites.subsurface(32*2, 80*2, 32*2, 32*2),
				sprites.subsurface(64*2, 80*2, 32*2, 32*2)
			]

		images.reverse()

		self.images = [] + images

		self.image = self.images.pop()

		timer.add(interval, lambda :self.update(), len(self.images) + 1)

	def draw(self):
		""" draw current explosion frame """
		self.screen.blit(self.image, self.position)

	def update(self):
		""" Advace to the next image """
		if len(self.images) > 0:
			self.image = self.images.pop()
		else:
			self.active = False
