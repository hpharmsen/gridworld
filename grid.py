import contextlib
import copy
import types
from functools import partial

with contextlib.redirect_stdout(None):  # Suppress Hello from Pygame community message
    import pygame

# Define some colors
LIGHTGRAY = (192, 192, 192)
GRAY = (128, 128, 128)
DARKGRAY = (45, 45, 45)

NONE = 0
LEFT = 1
TOP = 2
RIGHT = 3
BOTTOM = 4


class GridBase:
    ''' Basic grid datastructure independent of any display code'''

    def __init__(self, width, height):
        self.__width = width  # Width and height in number of cells
        self.__height = height
        self.__grid = [['' for x in range(self.width)] for y in range(self.height)]

    @classmethod
    def from_grid(cls, grid):
        ''' Alternative constructor, creat from another grid '''
        newgrid = cls(grid.width, grid.height)
        newgrid.__grid = copy.deepcopy(grid.grid)
        return newgrid

    @property
    def width(self):
        return self.__width

    @property
    def height(self):
        return self.__height

    @property
    def grid(self):
        return self.__grid

    def __getitem__(self, coo):
        ''' Makes it possible to access the grid like a 2-array'''
        x, y = coo
        try:
            return self.grid[y][x]
        except:
            return ''

    def __setitem__(self, coo, value):
        ''' Makes it possible to update the grid like a 2-array'''
        x, y = coo
        try:
            self.grid[y][x] = value
        except:
            pass


class Grid(GridBase):
    def __init__(
        self,
        width,
        height,
        cellwidth,
        cellheight,
        margin=0,
        title='',
        itemcolor=DARKGRAY,
        cellcolor=LIGHTGRAY,
        margincolor=DARKGRAY,
        item_fontname=None,
        framerate=60,
        sidebar_position=NONE,
        sidebar_size=0,
        full_screen=False,
    ):

        super().__init__(width, height)
        self.__cellwidth = cellwidth
        self.__cellheight = cellheight
        self.__margin = margin
        self.__itemcolor = itemcolor
        self.__cellcolor = cellcolor
        self.__margincolor = margincolor
        self.__framerate = framerate
        self.__sidebar_position = sidebar_position
        self.__sidebar_size = sidebar_size
        self.__sidebar_color = DARKGRAY
        self.__full_screen = full_screen
        self.__update_automatic = True  # No need to manually update or flip
        self.__update_fullscreen = (
            True
        )  # Full screen flip each frame. Set to False for only redrawing the effected area

        self.draw_actions = {}  # dict of symbol/function pairs that indicate how to draw each symbol

        pygame.init()
        pygame.display.set_caption(title)
        self.set_screen_dimensions()
        self.clock = pygame.time.Clock()

        pygame.font.init()
        item_fontname = item_fontname if item_fontname else pygame.font.get_default_font()
        self.font = pygame.font.Font(item_fontname, int(cellheight * 0.88))

        # Empty methods that can be set by the user
        self.timer_action = lambda self: None
        self.key_action = lambda self, key: None
        self.mouse_click_action = lambda self, pos: None
        self.cell_click_action = lambda self, cell: None
        self.update_sidebar_action = lambda self: None

    def set_screen_dimensions(self):
        sidebar_width = self.sidebar_size if self.sidebar_position in (LEFT, RIGHT) else 0
        sidebar_height = self.sidebar_size if self.sidebar_position in (TOP, BOTTOM) else 0
        if self.full_screen:
            infoObject = pygame.display.Info()
            self.oldcellwidth = self.cellwidth
            self.cellwidth = int((infoObject.current_w - sidebar_width) / self.width - self.margin)
            self.cellheght = int(self.cellheight * self.cellwidth / self.oldcellwidth)
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            screen_size = (
                self.width * (self.cellwidth + self.margin) + self.margin + sidebar_width,
                self.height * (self.cellheight + self.margin) + self.margin + sidebar_height,
            )
            self.screen = pygame.display.set_mode(screen_size)

    ###### Getting and setting values #####

    def __setitem__(self, coo, value):
        ''' Sets a grid value like a 2D array and redraws the cell if requested '''
        super().__setitem__(coo, value)
        if self.update_automatic:
            self.redraw_cell(*coo)

    # Cell size

    @property
    def cellwidth(self):
        return self.__cellwidth

    @property
    def cellheight(self):
        return self.__cellheight

    @property
    def margin(self):
        return self.__margin

    # Margins between the cells

    @margin.setter
    def margin(self, value):
        self.__margin = value

    @property
    def margincolor(self):
        return self.__margincolor

    @margincolor.setter
    def margincolor(self, value):
        self.__margincolor = value

    # Looks of the cells

    @property
    def cellcolor(self):
        return self.__cellcolor

    @cellcolor.setter
    def cellcolor(self, value):
        self.__cellcolor = value

    @property
    def itemcolor(self):
        return self.__itemcolor

    @itemcolor.setter
    def itemcolor(self, value):
        self.__itemcolor = value

    @property
    def itemfont(self):
        return self.__itemfont

    @itemfont.setter
    def itemfont(self, value):
        self.__itemfont = value

    @property
    def sidebar_position(self):
        return self.__sidebar_position

    @sidebar_position.setter
    def sidebar_position(self, value):
        self.__sidebar_position = value

    @property
    def sidebar_size(self):
        return self.__sidebar_size

    @sidebar_size.setter
    def sidebar_size(self, value):
        self.__sidebar_size = value

    @property
    def sidebar_color(self):
        return self.__sidebar_color

    @sidebar_color.setter
    def sidebar_color(self, value):
        self.__sidebar_color = value

    # Display and update settings

    @property
    def full_screen(self):
        return self.__full_screen

    @full_screen.setter
    def full_screen(self, value):
        self.__full_screen = value

    @property
    def update_automatic(self):
        return self.__update_automatic

    @update_automatic.setter
    def update_automatic(self, value):
        self.__update_automatic = value

    @property
    def update_fullscreen(self):
        return self.__update_fullscreen

    @update_fullscreen.setter
    def update_fullscreen(self, value):
        self.__update_fullscreen = value

    @property
    def framerate(self):
        return self.__framerate

    @framerate.setter
    def framerate(self, value):
        self.__framerate = value

    ##### User overwritable actions #####

    @property
    def timer_action(self):
        return self.__timer_action

    @timer_action.setter
    def timer_action(self, function):
        self.__timer_action = types.MethodType(function, self)

    @property
    def key_action(self):
        return self.__key_action

    @key_action.setter
    def key_action(self, function):
        self.__key_action = types.MethodType(function, self)

    @property
    def mouse_click_action(self):
        return self.__mouse_click_action

    @mouse_click_action.setter
    def mouse_click_action(self, function):
        self.__mouse_click_action = types.MethodType(function, self)

    @property
    def cell_click_action(self):
        return self.__cell_click_action

    @cell_click_action.setter
    def cell_click_action(self, function):
        self.__cell_click_action = types.MethodType(function, self)

    @property
    def update_sidebar_action(self):
        return self.__update_sidebar_action

    @update_sidebar_action.setter
    def update_sidebar_action(self, function):
        self.__update_sidebar_action = types.MethodType(function, self)

    ##### Drawing functions #####

    def redraw(self):
        self.screen.fill(self.margincolor)
        self.redraw_area(0, 0, self.width, self.height)
        self.update_sidebar_action()

    def redraw_cell(self, left, top):
        self.redraw_area(left, top, 1, 1)

    def redraw_area(self, left, top, width, height):
        for y in range(top, top + height):
            for x in range(left, left + width):
                self.__draw_cell(x, y)
        cell_dimensions = self.cell_dimensions(left, top, width, height)
        if self.update_automatic:
            if self.update_fullscreen:
                pygame.display.flip()
            else:
                pygame.display.update(cell_dimensions)

    def __draw_cell(self, x, y):
        cell_dimensions = self.cell_dimensions(x, y)
        pygame.draw.rect(self.screen, self.cellcolor, cell_dimensions)  # cell background
        draw_action = self.draw_actions.get(self[x, y])
        if not draw_action:
            # Drawing a character is the default
            draw_action = partial(self.draw_character_cell, character=self[x, y])
        draw_action(cell_dimensions)

    def draw_character_cell(self, cell_dimensions, character='?'):
        cell = pygame.draw.rect(self.screen, self.cellcolor, cell_dimensions)
        text = self.font.render(character, True, self.itemcolor)
        text_rect = text.get_rect()
        text_rect.center = cell.center
        self.screen.blit(text, text_rect)

    def clear_sidebar(self, color=None):
        if not color:
            color = self.sidebar_color
        pygame.draw.rect(self.screen, color, self.get_sidebar_dimensions())

    ##### Other properties #####

    def cell_dimensions(self, x, y, w=1, h=1):
        cell_x = (self.margin + self.cellwidth) * x + self.margin
        if self.sidebar_position == LEFT:
            cell_x += self.sidebar_size
        cell_y = (self.margin + self.cellheight) * y + self.margin
        if self.sidebar_position == TOP:
            cell_y += self.sidebar_size
        return (
            cell_x,
            cell_y,
            (self.cellwidth + self.margin) * w - self.margin,
            (self.cellheight + self.margin) * h - self.margin,
        )

    def cell_at_position(self, pos):
        cell_x, cell_y = pos
        if self.sidebar_position == LEFT:
            cell_x -= self.sidebar_size
        if self.sidebar_position == TOP:
            cell_y -= self.sidebar_size
        x = cell_x // (self.cellwidth + self.margin)
        y = cell_y // (self.cellheight + self.margin)
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return None
        return (x, y)

    def set_drawaction(self, symbol, action):
        self.draw_actions[symbol] = action

    def get_sidebar_dimensions(self):
        w, h = pygame.display.get_surface().get_size()
        s = self.sidebar_size
        if self.sidebar_position == TOP:
            return (0, 0, w, s)
        elif self.sidebar_position == RIGHT:
            return (w - s, 0, s, h)
        elif self.sidebar_position == BOTTOM:
            return (0, h - s, w, s)
        else:  # LEFT
            return (0, 0, s, h)

    def to_string(self):
        res = ''
        for y in range(self.height):
            for x in range(self.width):
                res += self[x, y] if self[x, y] else ' '
            res += '\n'
        res += '\n'
        return res

    def load(self, filepath):
        with open(filepath) as f:
            for y in range(self.height):
                line = f.readline()
                for x, char in enumerate(line):
                    self[x, y] = char

    def save(self, filepath):
        with open(filepath, 'w') as f:
            f.write(self.to_string())

    def snapshot(self):
        return GridBase.from_grid(self)

    def print(self):
        print(self.to_string())

    def done(self):
        # Close the window and quit.
        pygame.quit()

    ##### Main loop #####

    def run(self):
        self.redraw()
        # -------- Main Program Loop -----------
        while True:
            for event in pygame.event.get():  # User did something
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_f:
                        self.full_screen = not self.full_screen
                        self.set_screen_dimensions()
                        self.redraw()
                    else:
                        self.key_action(event.key)
                elif event.type == pygame.MOUSEBUTTONUP:
                    pos = pygame.mouse.get_pos()
                    self.mouse_click_action(pos)
                    coo = self.cell_at_position(pos)
                    if coo:
                        self.cell_click_action(coo)
                elif event.type == pygame.QUIT:  # If user clicked close
                    pygame.quit()
                    return
                elif event.type == pygame.ACTIVEEVENT:
                    self.redraw()

            # --- Game logic
            self.timer_action()

            # --- Limit to x frames per second
            self.clock.tick(self.framerate)


if __name__ == '__main__':
    grid = Grid(3, 3, 90, 90, title='Tic Tac Toe', margin=1)
    grid[0, 0] = 'O'
    grid[1, 1] = 'X'
    grid[2, 1] = 'O'
    grid[2, 2] = 'X'
    grid.run()
