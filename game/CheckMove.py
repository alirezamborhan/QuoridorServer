"""Contains a function to check Quoridor game moves.
Has been put in a separate file for convenience.
Now after any changed it can simply be copied to the client project.
"""

from copy import deepcopy


def check_win(main_grid, player):
    """Function to check if the game has been won."""
    # Extract player coordinations.
    for i in range(len(main_grid)):
        if player in main_grid[i]:
            py = i
            px = main_grid[i].index(player)
    if player == 1 and py == 8:
        return True
    if player == 2 and py == 0:
        return True
    if player == 3 and px == 8:
        return True
    if player == 4 and px == 0:
        return True
    return False

def _check_move_conditions(x, y, px, py, wallh_grid,
                           wallv_grid, main_grid):
    """Check conditions for moving the pawn."""
    if (
        # Move up:
        (y == py-1 and x == px and wallh_grid[y][x] == 0) or
        # Jump pawn up:
        (y == py-2 and x == px and wallh_grid[y][x] == 0 and
         wallh_grid[y+1][x] == 0 and main_grid[y+1][x] > 0) or
        # Move down:
        (y == py+1 and x == px and wallh_grid[py][px] == 0) or
        # Jump pawn down:
        (y == py+2 and x == px and wallh_grid[py][px] == 0 and
         wallh_grid[py+1][px] == 0 and main_grid[y-1][x] > 0) or
        # Move left:
        (y == py and x == px-1 and wallv_grid[y][x] == 0) or
        # Jump pawn left:
        (y == py and x == px-2 and wallv_grid[y][x] == 0 and
         wallv_grid[y][x+1] == 0 and main_grid[y][x+1] > 0) or
        # Move right:
        (y == py and x == px+1 and wallv_grid[py][px] == 0) or
        # Jump pawn right:
        (y == py and x == px+2 and wallv_grid[py][px] == 0 and
         wallv_grid[py][px+1] == 0 and main_grid[y][x-1] > 0) or
        # Jump northwest when path blocked twice above
        (y == py-1 and x == px-1 and main_grid[py-1][px] > 0 and
         wallh_grid[py-1][px] == 0 and
         (py == 1 or wallh_grid[py-2][px] == 1 or main_grid[py-2][px] > 0) and
         wallv_grid[py-1][px-1] == 0) or
        # Jump northwest when path blocked twice on left
        (y == py-1 and x == px-1 and main_grid[py][px-1] > 0 and
         wallv_grid[py][px-1] == 0 and
         (px == 1 or wallv_grid[py][px-2] == 1 or main_grid[py][px-2] > 0) and
         wallh_grid[py-1][px-1] == 0) or
        # Jump southwest when path blocked twice below
        (y == py+1 and x == px-1 and main_grid[py+1][px] > 0 and
         wallh_grid[py][px] == 0 and
         (py == 7 or wallh_grid[py+1][px] == 1 or main_grid[py+2][px] > 0) and
         wallv_grid[py+1][px-1] == 0) or
        # Jump southwest when path blocked twice on left
        (y == py+1 and x == px-1 and main_grid[py][px-1] > 0 and
         wallv_grid[py][px] == 0 and
         (px == 1 or wallv_grid[py][px-2] == 1 or main_grid[py][px-2] > 0) and
         wallh_grid[py][px-1] == 0) or
        # Jump northeast when path blocked twice above
        (y == py-1 and x == px+1 and main_grid[py-1][px] > 0 and
         wallh_grid[py-1][px] == 0 and
         (py == 1 or wallh_grid[py-2][px] == 1 or main_grid[py-2][px] > 0) and
         wallv_grid[py-1][px] == 0) or
        # Jump northeast when path blocked twice on right
        (y == py-1 and x == px+1 and main_grid[py][px+1] > 0 and
         wallv_grid[py][px] == 0 and
         (px == 7 or wallv_grid[py][px+1] == 1 or main_grid[py][px+2] > 0) and
         wallh_grid[py-1][px+1] == 0) or
        # Jump southeast when path blocked twice below
        (y == py+1 and x == px+1 and main_grid[py+1][px] > 0 and
         wallh_grid[py][px] == 0 and
         (py == 7 or wallh_grid[py+1][px] == 1 or main_grid[py+2][px] > 0) and
         wallv_grid[py+1][px] == 0) or
        # Jump southeast when path blocked twice on right
        (y == py+1 and x == px+1 and main_grid[py][px+1] > 0 and
         wallv_grid[py][px] == 0 and
         (px == 7 or wallv_grid[py][px+1] == 1 or main_grid[py][px+2] > 0) and
         wallh_grid[py][px+1] == 0)
):
          return True
    return False

def _check_surrounded(main_grid, wallh_grid, wallv_grid,
                      player, checked=[]):
    """Recursive function to check to see if walls block players' path.
Returns true if the player's path is blocked.
"""
    if check_win(main_grid, player):
        return False
    checked.append(main_grid)
    # Extract player coordinations.
    for i in range(len(main_grid)):
        if player in main_grid[i]:
            py = i
            px = main_grid[i].index(player)
    for move in [
            # (Condition, X, Y)
            # Normal up, down, left, right moves
            (py > 0, px, py-1),
            (py < 8, px, py+1),
            (px > 0, px-1, py),
            (px < 8, px+1, py),
            # Jumping players
            (py > 1, px, py-2),
            (py < 7, px, py+2),
            (px > 1, px-2, py),
            (px < 7, px+2, py),
            # Jumping when blocked twice
            (py > 0 and px > 0, px-1, py-1),
            (py < 8 and px > 0, px-1, py+1),
            (py > 0 and px < 8, px+1, py-1),
            (py < 8 and px < 8, px+1, py+1),
]:
        if (move[0] and main_grid[move[2]][move[1]] == 0 and
              _check_move_conditions(move[1], move[2], px, py,
                                     wallh_grid, wallv_grid, main_grid)):
            main_grid_copy = deepcopy(main_grid)
            main_grid_copy[py][px] = 0
            main_grid_copy[move[2]][move[1]] = player
            if (main_grid_copy not in checked and
                not _check_surrounded(main_grid_copy, wallh_grid,
                                      wallv_grid, player, checked=checked)):
                  return False
    return True

def check_move(main_grid, wallh_grid, wallv_grid,
               wallfills_grid, move, player, walls):
    """Check to see if game move is legal. Return True if so."""
    # Extract destination coordinations.
    x = move["x"]
    y = move["y"]
    # Extract player coordinations and list of players.
    players = (1, 2)
    for i in range(len(main_grid)):
        if player in main_grid[i]:
            py = i
            px = main_grid[i].index(player)
        if 4 in main_grid[i]:
            players = (1, 2, 3, 4)

    if (move["type"] == "move"
        and main_grid[y][x] == 0
        and _check_move_conditions(x, y, px, py,
                                   wallh_grid, wallv_grid, main_grid)):
          return True

    if move["type"] == "wall" and move["direction"] == "h":
        wallh_grid_copy = deepcopy(wallh_grid)
        wallh_grid_copy[y][x] = 1
        wallh_grid_copy[y][x+1] = 1
        if (wallh_grid[y][x] == 0 and wallh_grid[y][x+1] == 0 and
            wallfills_grid[y][x] == 0 and walls[player] > 0 and
            all([not _check_surrounded(main_grid, wallh_grid_copy, wallv_grid,
                                       p, checked=list()) for p in players])):
                return True

    if move["type"] == "wall" and move["direction"] == "v":
        wallv_grid_copy = deepcopy(wallv_grid)
        wallv_grid_copy[y][x] = 1
        wallv_grid_copy[y+1][x] = 1
        if (wallv_grid[y][x] == 0 and wallv_grid[y+1][x] == 0 and
            wallfills_grid[y][x] == 0 and walls[player] > 0 and
            all([not _check_surrounded(main_grid, wallh_grid, wallv_grid_copy,
                                       p, checked=list()) for p in players])):
                return True

    return False
