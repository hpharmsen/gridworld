import contextlib
import copy
import datetime
from functools import partial

with contextlib.redirect_stdout(None):  # Suppress Hello from Pygame community message
    import pygame

logging = False
def log(*args):
    global logging
    if logging:
        print(datetime.datetime.now().time(), ' '.join([str(a) for a in args]))

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
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [['' for x in range(self.width)] for y in range(self.height)]

    @classmethod
    def from_grid(cls, grid):
        newgrid = cls(grid.width, grid.height)
        newgrid.grid = copy.deepcopy(grid.grid)
        return newgrid

    def __getitem__(self, coo):
        x, y = coo
        try:
            return self.grid[y][x]
        except:
            return ''

    def __setitem__(self, coo, value):
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
        itemfont=None,
        framerate=60,
        statusbar_position = NONE,
        statusbar_size = 0,
        full_screen = False
    ):

        super().__init__(width, height)
        self.cellwidth = cellwidth
        self.cellheight = cellheight
        self.margin = margin
        self.itemcolor = itemcolor
        self.cellcolor = cellcolor
        self.margincolor = margincolor
        self.itemfont = itemfont
        self.framerate = framerate
        self.statusbar_position = statusbar_position
        self.statusbar_size = statusbar_size
        self.statusbar_color = DARKGRAY
        self.full_screen = full_screen

        self.draw_actions = {}  # dict of symbol/function pairs that indicate how to draw each symbol
        self.auto_update = False # Weather to redraw the screen with every change in the grid
        self.update_automatic = True # No need to manually update or flip
        self.update_fullscreen = True # Full screen flip each frame. Set to False for only redrawing the effected area

        pygame.init()
        pygame.display.set_caption(title)
        self.set_screen_dimensions()
        self.clock = pygame.time.Clock()

        pygame.font.init()
        self.itemfont = itemfont if itemfont else pygame.font.get_default_font()
        self.font = pygame.font.Font(self.itemfont, int(cellheight * 0.88))

    def set_screen_dimensions(self):
        statusbar_width = self.statusbar_size if self.statusbar_position in (LEFT,RIGHT) else 0
        statusbar_height = self.statusbar_size if self.statusbar_position in (TOP,BOTTOM) else 0
        if self.full_screen:
            infoObject = pygame.display.Info()
            self.oldcellwidth = self.cellwidth
            self.cellwidth = int((infoObject.current_w-statusbar_width) / self.width - self.margin)
            self.cellheght = int(self.cellheight * self.cellwidth / self.oldcellwidth)
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            screen_size = (
                self.width * (self.cellwidth + self.margin) + self.margin + statusbar_width,
                self.height * (self.cellheight + self.margin) + self.margin + statusbar_height,
            )
            self.screen = pygame.display.set_mode(screen_size)


    def __setitem__(self, coo, value):
        log('start_set')
        super().__setitem__(coo,value)
        if self.auto_update:
            self.redraw_cell(*coo)
        log('end_set')

    def frame_action(self, _):
        pass  # Should be overwritten by using program

    def key_action(self, _, key):
        pass  # Should be overwritten by using program


    def redraw(self):
        log('redraw')
        self.screen.fill(self.margincolor)
        self.redraw_area(0,0,self.width,self.height)
        log('end_redraw')

    def redraw_area(self, left, top, width, height ):
        log( 'redraw_area' )
        for y in range(top, top+height):
            for x in range(left, left+width):
                log('draw_cell')
                self.draw_cell(x, y)
        cell_dimensions = self.cell_dimensions(left, top, width, height)
        if self.update_automatic:
            if self.update_fullscreen:
                log('flip')
                pygame.display.flip()
            else:
                log('update', cell_dimensions)
                pygame.display.update(cell_dimensions)
            #log('clock_redraw_area')
            #self.clock.tick(self.framerate)
        log('end_redraw_area')

    def redraw_cell(self, left, top):
        self.redraw_area(left,top,1,1)

    def run(self):
        self.redraw()
        # -------- Main Program Loop -----------
        while True:
            for event in pygame.event.get():  # User did something
                if event.type == pygame.KEYDOWN:
                    if  event.key == pygame.K_f:
                        self.full_screen = not self.full_screen
                        self.set_screen_dimensions()
                        self.redraw()
                    else:
                        self.key_action(self, event.key)
                elif event.type == pygame.QUIT:  # If user clicked close
                    pygame.quit()
                    return
                elif event.type == pygame.ACTIVEEVENT:
                    self.redraw()

            # --- Game logic
            self.frame_action(self)

            # --- Limit to x frames per second
            self.clock.tick(self.framerate)

    def cell_dimensions(self,x,y,w=1,h=1):
        cell_x = (self.margin + self.cellwidth) * x + self.margin
        if self.statusbar_position == LEFT:
            cell_x += self.statusbar_size
        cell_y = (self.margin + self.cellheight) * y + self.margin
        if self.statusbar_position == TOP:
            cell_y += self.statusbar_size
        return cell_x,cell_y, (self.cellwidth+self.margin)*w-self.margin, (self.cellheight+self.margin)*h-self.margin

    def draw_cell(self, x, y):
        cell_dimensions = self.cell_dimensions(x,y)
        draw_action = self.draw_actions.get(self[x, y])
        if not draw_action:
            draw_action = partial(draw_character_cell, character=self[x, y])
        draw_action(self, cell_dimensions)

    def set_drawaction(self, symbol, action):
        self.draw_actions[symbol] = action


    def get_statusbar_dimensions(self):
        w, h = pygame.display.get_surface().get_size()
        s = self.statusbar_size
        if self.statusbar_position == TOP:
            return (0, 0, w, s)
        elif self.statusbar_position == RIGHT:
            return (w-s, 0, s, h)
        elif self.statusbar_position == BOTTOM:
            return (0, h-s, w, s)
        else: # LEFT
            return (0,0,s,h)

    def clear_statusbar(self, color=None):
        if not color:
            color = self.statusbar_color
        pygame.draw.rect(self.screen, color, self.get_statusbar_dimensions())

    def to_string(self):
        res = ''
        for y in range(self.height):
            for x in range(self.width):
                val = self[x, y] if self[x, y] else '.'
                res += val + ' '
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


def draw_character_cell(grid, cell_dimensions, character='?'):
    cell = pygame.draw.rect(grid.screen, grid.cellcolor, cell_dimensions)
    text = grid.font.render(character, True, grid.itemcolor)
    text_rect = text.get_rect()
    text_rect.center = cell.center
    grid.screen.blit(text, text_rect)


if __name__ == '__main__':
    grid = Grid(3, 3, 90, 90, title='Tic Tac Toe', margin=1)
    grid[0, 0] = 'O'
    grid[1, 1] = 'X'
    grid[2, 1] = 'O'
    grid[2, 2] = 'X'
    grid.run()
