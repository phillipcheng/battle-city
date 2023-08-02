import pygame


class joystick_handler(object):

    def __init__(self, id):
        (self.DIR_FIRE, self.DIR_UP, self.DIR_RIGHT, self.DIR_DOWN, self.DIR_LEFT, self.DIR_HELMET,
         self.DIR_FREEZE, self.DIR_ALL_FIRE, self.DIR_TOGGLE_TRICK) = range(9)
        self.prev_x = 0
        self.prev_y = 0
        self.prev_event_key = None
        self.id = id
        self.joy = pygame.joystick.Joystick(id)
        self.name = self.joy.get_name()
        self.joy.init()
        self.numaxes = self.joy.get_numaxes()
        self.numbuttons = self.joy.get_numbuttons()

        self.axis = []
        for i in range(self.numaxes):
            self.axis.append(self.joy.get_axis(i))

        self.button = []
        for i in range(self.numbuttons):
            self.button.append(self.joy.get_button(i))

    def get_event_key(self, player_index, button_func):
        if player_index == 0:
            if button_func == self.DIR_FIRE:
                return pygame.K_SPACE
            elif button_func == self.DIR_UP:
                return pygame.K_UP
            elif button_func == self.DIR_DOWN:
                return pygame.K_DOWN
            elif button_func == self.DIR_RIGHT:
                return pygame.K_RIGHT
            elif button_func == self.DIR_LEFT:
                return pygame.K_LEFT
            elif button_func == self.DIR_HELMET:
                return pygame.K_o
            elif button_func == self.DIR_FREEZE:
                return pygame.K_p
            elif button_func == self.DIR_ALL_FIRE:
                return pygame.K_l
            elif button_func == self.DIR_TOGGLE_TRICK:
                return pygame.K_COMMA
            else:
                return -1
        #pygame.K_f, pygame.K_w, pygame.K_d, pygame.K_s, pygame.K_a, pygame.K_z, pygame.K_x
        elif player_index == 1:
            if button_func == self.DIR_FIRE:
                return pygame.K_f #
            elif button_func == self.DIR_UP:
                return pygame.K_w #
            elif button_func == self.DIR_DOWN:
                return pygame.K_s #
            elif button_func == self.DIR_RIGHT:
                return pygame.K_d #
            elif button_func == self.DIR_LEFT:
                return pygame.K_a #
            elif button_func == self.DIR_HELMET:
                return pygame.K_z #
            elif button_func == self.DIR_FREEZE:
                return pygame.K_x #
            elif button_func == self.DIR_ALL_FIRE:
                return pygame.K_c #
            # elif button_func == self.DIR_TOGGLE_TRICK:
            #     return pygame.K_v
            else:
                return -1
        else:
            return -1

    '''
    translate joystick event to key_board event
    player-0: [pygame.K_SPACE, pygame.K_UP, pygame.K_RIGHT, pygame.K_DOWN, pygame.K_LEFT]
    player-1: [102, 119, 100, 115, 97]
    '''

    def translate_event(self):
        numaxes = self.numaxes
        numbuttons = self.numbuttons
        new_event = None
        new_event_key = None

        for axis_i in range(numaxes):
            if axis_i == 0:  # x
                axis_x = self.joy.get_axis(axis_i)
                if axis_x >= 0.9:  # left
                    new_event_key = self.get_event_key(self.id, self.DIR_RIGHT)
                    new_event = pygame.event.Event(pygame.KEYDOWN, key=new_event_key)
                    pygame.event.post(new_event)
                elif axis_x < -0.9:  # right
                    new_event_key = self.get_event_key(self.id, self.DIR_LEFT)
                    new_event = pygame.event.Event(pygame.KEYDOWN, key=new_event_key)
                    pygame.event.post(new_event)
                else:
                    if self.prev_x != axis_x:
                        new_event_key = self.get_event_key(self.id, self.DIR_RIGHT)
                        new_event = pygame.event.Event(pygame.KEYUP, key=new_event_key)
                        pygame.event.post(new_event)
                        new_event_key = self.get_event_key(self.id, self.DIR_LEFT)
                        new_event = pygame.event.Event(pygame.KEYUP, key=new_event_key)
                        pygame.event.post(new_event)
                self.prev_x = axis_x
            elif axis_i == 1:  # y
                axis_y = self.joy.get_axis(axis_i)
                if axis_y >= 0.9:  # down
                    new_event_key = self.get_event_key(self.id, self.DIR_DOWN)
                    new_event = pygame.event.Event(pygame.KEYDOWN, key=new_event_key)
                    pygame.event.post(new_event)
                elif axis_y <= -0.9:  # up
                    new_event_key = self.get_event_key(self.id, self.DIR_UP)
                    new_event = pygame.event.Event(pygame.KEYDOWN, key=new_event_key)
                    pygame.event.post(new_event)
                else:
                    if self.prev_y != axis_y:
                        new_event_key = self.get_event_key(self.id, self.DIR_UP)
                        new_event = pygame.event.Event(pygame.KEYUP, key=new_event_key)
                        pygame.event.post(new_event)
                        new_event_key = self.get_event_key(self.id, self.DIR_DOWN)
                        new_event = pygame.event.Event(pygame.KEYUP, key=new_event_key)
                        pygame.event.post(new_event)
                self.prev_y = axis_y
        # button 4: select, button 9: L, button 10: R
        # button 0: A, button 1: B, button 2: X, button 3: Y
        for i in range(numbuttons):
            button = self.joy.get_button(i)
            if i == 1: #B
                if button == 1:
                    # print(f"joy:{self.id} Button {i:>2} value: {button}")
                    new_event_key = self.get_event_key(self.id, self.DIR_FIRE)
                    new_event = pygame.event.Event(pygame.KEYDOWN, key=new_event_key)
                    pygame.event.post(new_event)
            elif i == 0: #A helmet
                if button == 1:
                    # print(f"joy:{self.id} Button {i:>2} value: {button}")
                    new_event_key = self.get_event_key(self.id, self.DIR_HELMET)
                    new_event = pygame.event.Event(pygame.KEYDOWN, key=new_event_key)
                    pygame.event.post(new_event)
            elif i == 2: #X freeze
                if button == 1:
                    # print(f"joy:{self.id} Button {i:>2} value: {button}")
                    new_event_key = self.get_event_key(self.id, self.DIR_FREEZE)
                    new_event = pygame.event.Event(pygame.KEYDOWN, key=new_event_key)
                    pygame.event.post(new_event)
            elif i == 3: #Y all fire
                if button == 1:
                    # print(f"joy:{self.id} Button {i:>2} value: {button}")
                    new_event_key = self.get_event_key(self.id, self.DIR_ALL_FIRE)
                    new_event = pygame.event.Event(pygame.KEYDOWN, key=new_event_key)
                    pygame.event.post(new_event)
            elif i == 4: #select toggle trick
                if button == 1:
                    # print(f"joy:{self.id} Button {i:>2} value: {button}")
                    new_event_key = self.get_event_key(self.id, self.DIR_TOGGLE_TRICK)
                    new_event = pygame.event.Event(pygame.KEYDOWN, key=new_event_key)
                    pygame.event.post(new_event)