"""Contains a function to check Quoridor game moves.
Has been put in a separate file for convenience.
Now after any changed it can simply be copied to the client project.
"""

def check_move(main_grid, wallh_grid, wallv_grid, wallfills_grid, move, player):
    """Check to see if game move is legal. Return True if so."""
    # Extract destination coordinations.
    x = move["x"]
    y = move["y"]
    # Extract player coordinations.
    for i in range(len(main_grid)):
        if player in main_grid[i]:
            py = i
            px = main_grid[i].index(player)

    if (move["type"] == "move"
       and main_grid[y][x] == 0
       and (
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
            wallv_grid[py][px+1] == 0 and main_grid[y][x-1] > 0)
)):
        return True

    if move["type"] == "wall":
        return True

    return False
