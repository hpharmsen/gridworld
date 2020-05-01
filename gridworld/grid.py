import contextlib
import copy
from functools import partial

with contextlib.redirect_stdout(None):  # Suppress Hello from Pygame community message
    import pygame  # Warm hello back to the Pygame community by the way.

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
    ''' Basic grid datastructure independent of any display code

        Grid is a 2D space with on each square a list of stacked items
        the items are characters.
        In most applications the list will be either empty (empty square) or contain a single element
        since often a square can contain but a single element.
        It can be accessed/set using setting grid[x,y].

        It is possible however to stack multiple elements on a square (think checkers or separating
        the background from the foreground.
        To add an extra element use grid.push[x,y]
        To access a certain level use grid[x,y,z].
        Without specifing z, the top element is always returned/replaced.
    '''

    def __init__(self, width, height):
        self.__width = width  # Width and height in number of cells
        self.__height = height
        self.clear_all()

    @classmethod
    def from_grid(cls, grid):
        ''' Alternative constructor, create from another grid '''
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
        ''' Makes it possible to access the grid like a 2D or 3D-array'''
        x, y, *z = coo
        z = z[0] if z != [] else -1
        try:
            return self.__grid[y][x][z]
        except:
            return None

    def __setitem__(self, coo, value):
        ''' Makes it possible to update the grid like a 2-array'''
        x, y, *z = coo

        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return  # Position is out of grid. Ignore set operation

        z = z[0] if z != [] else -1

        if value == None:
            self.__grid[y][x] = []  # clear the square
        elif self.__grid[y][x] == [] or z == len(self.__grid[y][x]):
            self.__grid[y][x] += [value]  # Add new value
        elif z > len(self.__grid[y][x]):
            raise Exception(
                f'You are tying to update element {z[0]} at position ({x},{y}) but ({x},{y}) contains only {len(self.__grid[y][x])} elements.'
            )
        else:
            self.__grid[y][x][z] = value  # Replace current value

    def push(self, coo, value):
        ''' Put an item on top of possible existing items at grid square'''
        x, y = coo

        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return  # Position is out of grid. Ignore push operation

        self.__grid[y][x] += [value]  # Add new value

    def pop(self, coo):
        ''' Put an item on top of possible existing items at grid square'''
        x, y = coo

        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return None  # Position is out of grid.

        value = self.__grid[y][x]
        self.__grid[y][x] = self.__grid[y][x][:-1]
        return value

    def clear(self, coo):
        ''' Delete all items from a square '''
        x, y = coo

        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return None  # Position is out of grid.

        self.__grid[y][x] = []

    def clear_all(self):
        self.__grid = [[[] for x in range(self.width)] for y in range(self.height)]


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
        font=None,
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
        self.font = font

        # Empty callbacks that can be set by the user
        self.__timer_action = lambda: None
        self.__key_action = lambda key: None
        self.__mouse_click_action = lambda pos: None
        self.__cell_click_action = lambda cell: None
        self.__update_sidebar_action = lambda: None

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
            self.redraw_cell(*coo[:2])

    def push(self, coo, value):
        ''' Sets a grid value on top of any existing values at a grid square '''
        super().push(coo, value)
        if self.update_automatic:
            self.redraw_cell(*coo[:2])

    def pop(self, coo):
        ''' Sets a grid value on top of any existing values at a grid square '''
        value = super().pop(coo)
        if self.update_automatic:
            self.redraw_cell(*coo[:2])
        return value

    def clear(self, coo):
        ''' Sets a grid value on top of any existing values at a grid square '''
        value = super().clear(coo)
        if self.update_automatic:
            self.redraw_cell(*coo[:2])

    # Cell size

    @property
    def cellwidth(self):
        return self.__cellwidth

    @cellwidth.setter
    def cellwidth(self, value):
        self.__cellwidth = value

    @property
    def cellheight(self):
        return self.__cellheight

    @cellheight.setter
    def cellheight(self, value):
        self.__cellheight = value

    # Margins between the cells

    @property
    def margin(self):
        return self.__margin

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
    def font(self):
        return self.__font_filename

    @font.setter
    def font(self, value):
        self.__font_filename = value
        self.__font = pygame.font.Font(value, int(self.cellheight * 0.88))

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

    ##### User overwritable callbacks #####

    def set_timer_action(self, function):
        self.__timer_action = function

    def set_key_action(self, function):
        self.__key_action = function

    def set_mouse_click_action(self, function):
        self.__mouse_click_action = function

    def set_cell_click_action(self, function):
        self.__cell_click_action = function

    def set_update_sidebar_action(self, function):
        self.__update_sidebar_action = function

    ##### Drawing functions #####

    def redraw(self):
        self.screen.fill(self.margincolor)
        self.redraw_area(0, 0, self.width, self.height)
        self.__update_sidebar_action()

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
        draw_action(self, cell_dimensions)

    def draw_character_cell(self, _, cell_dimensions, character='?'):
        cell = self.draw_background(_, cell_dimensions, self.cellcolor)
        text = self.__font.render(character, True, self.itemcolor)
        text_rect = text.get_rect()
        text_rect.center = cell.center
        self.screen.blit(text, text_rect)

    def draw_background(self, _, cell_dimensions, color=GRAY):
        try:
            return pygame.draw.rect(self.screen, color, cell_dimensions)
        except:
            pass

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

    def load(self, filepath, resize=False):
        with open(filepath) as f:
            lines = f.readlines()
        ua = self.update_automatic
        self.update_automatic = False
        if resize:
            w = max([len(line) for line in lines]) - 1
            h = len(lines)
            super().__init__(w, h)
            self.set_screen_dimensions()
        for y, line in enumerate(lines):
            for x, char in enumerate(line[:-1]):
                self[x, y] = char
        self.update_automatic = ua

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
                        self.__key_action(event.key)
                elif event.type == pygame.MOUSEBUTTONUP:
                    pos = pygame.mouse.get_pos()
                    self.__mouse_click_action(pos)
                    coo = self.cell_at_position(pos)
                    if coo:
                        self.__cell_click_action(coo)
                elif event.type == pygame.QUIT:  # If user clicked close
                    pygame.quit()
                    return
                elif event.type == pygame.ACTIVEEVENT:
                    self.redraw()

            # --- Game logic
            self.__timer_action()

            # --- Limit to x frames per second
            self.clock.tick(self.framerate)


if __name__ == '__main__':
    grid = Grid(3, 3, 90, 90, title='Tic Tac Toe', margin=1)
    grid[0, 0] = 'O'
    grid[1, 1] = 'X'
    grid[2, 1] = 'O'
    grid[2, 2] = 'X'
    grid.run()
