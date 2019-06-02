import random
from functools import partial
from grid import Grid
import pygame

game_active = True


def cell_click(pos):
    global game_active
    x, y = pos
    if game_active:
        grid[x, y] = 'X'
        if check_win(grid, 'X'):
            pygame.display.flip()
            game_active = False
        else:
            while grid[x, y]:  # search for empty space to put an O
                x = random.randint(0, 2)
                y = random.randint(0, 2)
            grid[x, y] = 'O'
            if check_win(grid, 'O'):
                pygame.display.flip()
                game_active = False
    else:
        # Start a new game
        for x in range(3):
            for y in range(3):
                grid[x, y] = ''
        grid.redraw()
        game_active = True


def check_win(grid, player_symbol):
    color = (0, 200, 0) if player_symbol == 'X' else (200, 0, 0)  # Green or Red
    screen_width = grid.width * (grid.cellwidth + grid.margin) - grid.margin
    screen_height = grid.height * (grid.cellheight + grid.margin) - grid.margin
    for i in range(3):
        # Check for vertical win
        if grid[i, 0] == grid[i, 1] == grid[i, 2] == player_symbol:
            x = int((i + 0.5) * grid.cellwidth)
            pygame.draw.line(grid.screen, color, (x, 0), (x, screen_height), 6)
            return True
        # Check for horizontal win
        if grid[0, i] == grid[1, i] == grid[2, i] == player_symbol:
            y = int((i + 0.5) * grid.cellheight)
            pygame.draw.line(grid.screen, color, (0, y), (screen_height, y), 6)
            return True
    # Check for diagonal win
    if grid[0, 0] == grid[1, 1] == grid[2, 2] == player_symbol:
        pygame.draw.line(grid.screen, color, (0, 0), (screen_width, screen_height), 6)
        return True
    if grid[2, 0] == grid[1, 1] == grid[0, 2] == player_symbol:
        pygame.draw.line(grid.screen, color, (0, screen_height), (screen_width, 0), 6)
        return True
    # Check for draw
    for x in range(3):
        for y in range(3):
            if not grid[x, y]:  # Empty space left. Play on
                return False
    return True


if __name__ == '__main__':
    grid = Grid(3, 3, 90, 90, title='Tic Tac Toe', margin=1)
    # grid.set_cell_click_action(partial(cell_click, grid=grid))
    grid.set_cell_click_action(cell_click)
    grid.run()
