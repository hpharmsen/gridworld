import sys
from grid import Grid, draw_character_cell, TOP, log
from functools import partial
import pygame
from queue import Queue

# https://csijh.github.io/wanderer/javascript/index.html

# TODO:
# - Split into Gridworld and Wanderer projects
# - All on GitHub
# - Dead by arrows en boulders
# - Persistent statusbar
# - Message by kill
# - Level chooser
# - center screen in full screen mode
# - Switch between update and flip
# - Win when exit and all money
# - Readme.md with dependencies and usage
# - implement balloons
# - implement monsters
# - implement time capsule and maximum moves


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (12, 192, 12)
RED = (255, 0, 0)
BLUE = (0, 0, 128)
LIGHTGRAY = (192, 192, 192)
GRAY = (128, 128, 128)
DARKGRAY = (45, 45, 45)
YELLOW = (192, 192, 0)
LIGHTBLUE = (100, 140, 255)

granite = '#'
brick = '='
earth = ':'
star = '*'
hero_sign = '@'
deflector_up = '/'
deflector_down = '\\'
arrow_left = '<'
arrow_right = '>'
boulder = 'O'
balloon = '^'
empty = ' '
teleport = 'T'
teleport_destination = 'A'
bomb = '!'


class Hero:

    def __init__(self, grid):
        self.grid = grid
        self.stars_to_go = 0
        for y in range(grid.height):
            for x in range(grid.width):
                if grid[x, y] == hero_sign:
                    self.x = x
                    self.y = y
                elif grid[x, y] == star:
                    self.stars_to_go += 1
                elif grid[x, y] == teleport_destination:
                    self.teleport_destination = (x, y)

    def move(self, movement):

        dx, dy = movement
        target = self.grid[self.x + dx, self.y + dy]

        def abs_move(x, y):
            fill_queue(self.x,self.y)
            fill_queue(x,y)
            grid[self.x, self.y] = ' '
            self.x = x
            self.y = y
            grid[x, y] = hero_sign

        def rel_move(dx, dy):
            abs_move(self.x + dx, self.y + dy)

        # leeg, earth -> move
        if target in (empty, earth):
            rel_move(dx, dy)

        # geld -> punten omhoog en move
        elif target == star:
            rel_move(dx, dy)
            self.stars_to_go -= 1
            sx,sy,sw,sh = grid.get_statusbar_dimensions()
            grid.clear_statusbar(DARKGRAY)
            text = f'{self.stars_to_go} bags to go'
            font = pygame.font.Font(grid.itemfont, 30)
            rendered = font.render(text, True, WHITE)
            #text_rect = text.get_rect()
            #text_rect.center = (x + w * pos[0] // 100, y + h * pos[1] // 100)
            grid.screen.blit(rendered, (sx,sy))

        # boulder of balloon en opzij en niks achter bolder/balloon -> move bolder/balloon en zelf
        elif target == boulder and dy == 0:
            if dx == -1 and grid[self.x - 2, self.y] == empty:
                grid[self.x - 2, self.y] = target
                rel_move(dx, dy)
            elif dx == 1 and grid[self.x + 2, self.y] == empty:
                grid[self.x + 2, self.y] = target
                rel_move(dx, dy)

        # arrow en omhoog/laag en niks achter arrow -> move arrow en zelf
        elif target in (arrow_left, arrow_right) and dx == 0:
            if dy == -1 and grid[self.x, self.y - 2] == empty:
                grid[self.x, self.y - 2] = target
                rel_move(dx, dy)
            elif dy == 1 and grid[self.x, self.y + 2] == empty:
                grid[self.x, self.y + 2] = target
                rel_move(dx, dy)

        # teleport -> teleport
        elif target == teleport:
            rel_move(dx, dy)
            abs_move(*self.teleport_destination)

        # bom -> dood
        elif target == bomb:
            sys.exit()


direction_map = {pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0), pygame.K_UP: (0, -1), pygame.K_DOWN: (0, 1)}
def key_action(grid, key):
    global direction_map, current_level
    log( 'key_action', key)
    if key == pygame.K_q:
        sys.exit()
    elif key==pygame.K_r:
        start_level(grid, current_level)
    move = direction_map.get(key)
    if move:
        hero.move(move)
    log('hero moved')

def fill_queue(x,y):
    # Check for items that might move
    for dx in range(-1,2):
        for dy in range(-1,2):
            if grid[x+dx,y+dy] != empty:
                action_queue.put( (x+dx,y+dy) )

def process_queue(grid):
    global action_queue

    def try_move(x,y,dx,dy):
        if grid[x + dx, y + dy] == empty:
            grid[x + dx, y + dy] = grid[x, y]
            grid[x, y] = empty
            fill_queue(x, y)
            fill_queue(x+dx, y+dy)
            return True
        return False

    if action_queue.list:
        log('process_queue')
    while action_queue.list:

        x, y = action_queue.get()
        symbol = grid[x,y]

        if symbol == boulder:
            if try_move(x,y,0,+1): # down
                return
            if grid[x,y+1] in (boulder,deflector_up) and grid[x-1,y]==empty and try_move(x,y,-1,+1): # down-left
                return
            if grid[x,y+1] in (boulder,deflector_down) and grid[x+1,y]==empty and try_move(x,y,+1,+1): # down-right
                return
        elif symbol == arrow_left:
            if try_move(x,y,-1,0): # left
                return
            if grid[x-1,y] in (boulder,deflector_down) and grid[x,y-1]==empty and try_move(x,y,-1,-1): # left-up
                return
            if grid[x-1,y] in (boulder,deflector_up) and grid[x,y+1]==empty and try_move(x,y,-1,+1): # left-down
                return
        elif symbol == arrow_right:
            if try_move(x,y,+1,0): # right
                return
            if grid[x+1,y] in (boulder,deflector_up) and grid[x,y-1]==empty and try_move(x,y,+1,-1): # right-up
                return
            if grid[x+1,y] in (boulder,deflector_down) and grid[x,y+1]==empty and try_move(x,y,+1,+1): # right-down
                return

## Basic drawing routines

def draw_ground(grid, cell_dimensions, color=GRAY):
    return pygame.draw.rect(grid.screen, color, cell_dimensions)


def draw_line(grid, cell_dimensions, fromcoo, tocoo, color, width):
    x, y, w, h = cell_dimensions
    pygame.draw.line(
        grid.screen,
        color,
        (x + w * fromcoo[0] // 100, y + h * fromcoo[1] // 100),
        (x + w * tocoo[0] // 100, y + h * tocoo[1] // 100),
        w * width // 100,
    )


def draw_circle(grid, cell_dimensions, pos, diameter, color=DARKGRAY):
    x, y, w, h = cell_dimensions
    pygame.draw.circle(grid.screen, color, (x + w * pos[0] // 100, y + h * pos[1] // 100), w * diameter // 200)


def draw_text(grid, cell_dimensions, text, pos, size, color):
    x, y, w, h = cell_dimensions
    font = pygame.font.Font(grid.itemfont, h * size // 100)
    text = font.render(text, True, WHITE)
    text_rect = text.get_rect()
    text_rect.center = (x + w * pos[0] // 100, y + h * pos[1] // 100)
    grid.screen.blit(text, text_rect)


# Specific drawing routines


def draw_boulder(grid, cell_dimensions):
    draw_ground(grid, cell_dimensions, LIGHTGRAY)
    draw_circle(grid, cell_dimensions, (50, 50), 80, color=(90, 48, 22))
    x,y,w,h = cell_dimensions
    cellx = int(x/(grid.cellwidth+grid.margin))
    celly = int(y/(grid.cellheight+grid.margin))
    draw_text(grid,cell_dimensions, f'{cellx},{celly}', (50,50), 29, WHITE)

def draw_bomb(grid, cell_dimensions):
    draw_ground(grid, cell_dimensions, LIGHTGRAY)
    draw_circle(grid, cell_dimensions, (50, 50), 70, BLACK)  # Bomb itself
    draw_circle(grid, cell_dimensions, (40, 40), 10, WHITE)  # White glow
    draw_line(grid, cell_dimensions, (50, 50), (85, 15), BLACK, 23)  # Fuse
    draw_line(grid, cell_dimensions, (80, 10), (90, 20), YELLOW, 23)  # Spark


def draw_down_line(grid, cell_dimensions):
    draw_ground(grid, cell_dimensions, LIGHTGRAY)
    draw_line(grid, cell_dimensions, (0, 0), (100, 100), GREEN, 10)


def draw_up_line(grid, cell_dimensions):
    draw_ground(grid, cell_dimensions, LIGHTGRAY)
    draw_line(grid, cell_dimensions, (0, 100), (100, 0), GREEN, 10)


def draw_money(grid, cell_dimensions):
    draw_ground(grid, cell_dimensions, LIGHTGRAY)
    draw_circle(grid, cell_dimensions, (50, 60), 60, LIGHTBLUE)  # Sack itself
    draw_line(grid, cell_dimensions, (40, 25), (60, 25), LIGHTBLUE, 15)
    draw_text(grid, cell_dimensions, '$', (50, 60), 36, WHITE)

class MyQueue():
    def __init__(self):
        self.list = []
    def put(self, item):
        self.list += [item]
        #print('PUT', item, len(self.list), self.list)
    def get(self):
        item = self.list[0]
        self.list = self.list[1:]
        #print('GET', item, grid[item], len(self.list), self.list)
        return item

def start_level(grid,level):
    global hero
    grid.auto_update = False
    grid.load(f'levels/level{level}.txt')
    grid.redraw()
    grid.auto_update = True
    hero = Hero(grid)

if __name__ == '__main__':
    current_level = 1
    grid = Grid(
        42, 18, 28, 28, title='test', margin=0, margincolor=GRAY, itemfont='/Library/Fonts/Arial.ttf', framerate=60,
        statusbar_position = TOP, statusbar_size = 34, full_screen = False
    )
    grid.set_drawaction('#', partial(draw_ground, color=(60, 60, 60)))
    grid.set_drawaction('=', partial(draw_ground, color=(70, 70, 70)))
    grid.set_drawaction(':', partial(draw_ground, color=(140, 120, 80)))
    grid.set_drawaction('\\', draw_down_line)
    grid.set_drawaction('O', draw_boulder)
    grid.set_drawaction('/', draw_up_line)
    grid.set_drawaction('!', draw_bomb)
    grid.set_drawaction('*', draw_money)
    grid.set_drawaction('<', partial(draw_character_cell, character='←'))
    grid.set_drawaction('>', partial(draw_character_cell, character='→'))
    grid.frame_action = process_queue
    grid.key_action = key_action

    start_level(grid,current_level)

    action_queue = MyQueue()
    grid.run()
