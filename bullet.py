import pygame

from explosion import Explosion


class Bullet():
    # direction constants
    (DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT) = range(4)

    # bullet's stated
    (STATE_REMOVED, STATE_ACTIVE, STATE_EXPLODING) = range(3)

    (OWNER_PLAYER, OWNER_ENEMY) = range(2)

    def __init__(self, level, position, direction, damage=100, speed=5, globals=None):

        self.globals=globals
        self.level = level
        self.direction = direction
        self.damage = damage
        self.owner = None
        self.owner_class = None

        # 1-regular everyday normal bullet
        # 2-can destroy steel
        self.power = 1

        self.image = self.globals.sprites.subsurface(75 * 2, 74 * 2, 3 * 2, 4 * 2)

        # position is player's top left corner, so we'll need to
        # recalculate a bit. also rotate image itself.
        if direction == self.DIR_UP:
            self.rect = pygame.Rect(position[0] + 11, position[1] - 8, 6, 8)
        elif direction == self.DIR_RIGHT:
            self.image = pygame.transform.rotate(self.image, 270)
            self.rect = pygame.Rect(position[0] + 26, position[1] + 11, 8, 6)
        elif direction == self.DIR_DOWN:
            self.image = pygame.transform.rotate(self.image, 180)
            self.rect = pygame.Rect(position[0] + 11, position[1] + 26, 6, 8)
        elif direction == self.DIR_LEFT:
            self.image = pygame.transform.rotate(self.image, 90)
            self.rect = pygame.Rect(position[0] - 8, position[1] + 11, 8, 6)

        self.explosion_images = [
            self.globals.sprites.subsurface(0, 80 * 2, 32 * 2, 32 * 2),
            self.globals.sprites.subsurface(32 * 2, 80 * 2, 32 * 2, 32 * 2),
        ]

        self.speed = speed

        self.state = self.STATE_ACTIVE

    def draw(self):
        """ draw bullet """
        if self.state == self.STATE_ACTIVE:
            self.globals.screen.blit(self.image, self.rect.topleft)
        elif self.state == self.STATE_EXPLODING:
            self.explosion.draw()

    def update(self):

        if self.state == self.STATE_EXPLODING:
            if not self.explosion.active:
                self.destroy()
                del self.explosion

        if self.state != self.STATE_ACTIVE:
            return

        """ move bullet """
        if self.direction == self.DIR_UP:
            self.rect.topleft = [self.rect.left, self.rect.top - self.speed]
            if self.rect.top < 0:
                if self.globals.play_sounds and self.owner == self.OWNER_PLAYER:
                    self.globals.sounds["steel"].play()
                self.explode()
                return
        elif self.direction == self.DIR_RIGHT:
            self.rect.topleft = [self.rect.left + self.speed, self.rect.top]
            if self.rect.left > (416 - self.rect.width):
                if self.globals.play_sounds and self.owner == self.OWNER_PLAYER:
                    self.globals.sounds["steel"].play()
                self.explode()
                return
        elif self.direction == self.DIR_DOWN:
            self.rect.topleft = [self.rect.left, self.rect.top + self.speed]
            if self.rect.top > (416 - self.rect.height):
                if self.globals.play_sounds and self.owner == self.OWNER_PLAYER:
                    self.globals.sounds["steel"].play()
                self.explode()
                return
        elif self.direction == self.DIR_LEFT:
            self.rect.topleft = [self.rect.left - self.speed, self.rect.top]
            if self.rect.left < 0:
                if self.globals.play_sounds and self.owner == self.OWNER_PLAYER:
                    self.globals.sounds["steel"].play()
                self.explode()
                return

        has_collided = False

        # check for collisions with walls. one bullet can destroy several (1 or 2)
        # tiles but explosion remains 1
        rects = self.level.obstacle_rects
        collisions = self.rect.collidelistall(rects)
        if collisions != []:
            for i in collisions:
                if self.level.hitTile(rects[i].topleft, self.power, self.owner == self.OWNER_PLAYER):
                    has_collided = True
        if has_collided:
            self.explode()
            return

        # check for collisions with other bullets
        for bullet in self.globals.bullets:
            if self.state == self.STATE_ACTIVE and bullet.owner != self.owner and bullet != self and self.rect.colliderect(
                    bullet.rect):
                self.destroy()
                self.explode()
                return

        # check for collisions with players
        for player in self.globals.players:
            if player.state == player.STATE_ALIVE and self.rect.colliderect(player.rect):
                if player.bulletImpact(self.owner == self.OWNER_PLAYER, self.damage, self.owner_class):
                    self.destroy()
                    return

        # check for collisions with enemies
        for enemy in self.globals.enemies:
            if enemy.state == enemy.STATE_ALIVE and self.rect.colliderect(enemy.rect):
                if enemy.bulletImpact(self.owner == self.OWNER_ENEMY, self.damage, self.owner_class):
                    self.destroy()
                    return

        # check for collision with castle
        if self.globals.castle.active and self.rect.colliderect(self.globals.castle.rect):
            self.globals.castle.destroy()
            self.destroy()
            return

    def explode(self):
        """ start bullets's explosion """
        if self.state != self.STATE_REMOVED:
            self.state = self.STATE_EXPLODING
            self.explosion = Explosion([self.rect.left - 13, self.rect.top - 13], self.globals.timer, self.globals.screen, self.globals.sprites, interval=None, images=self.explosion_images)

    def destroy(self):
        self.state = self.STATE_REMOVED
