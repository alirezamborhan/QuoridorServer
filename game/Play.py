"""This module includes server-side functions needed to play Quoridor."""

import json
from random import randint

from django.contrib.sessions.models import Session
from game.models import TwoPlayerGame, FourPlayerGame

from CheckMove import check_move


def new(users, requested_players):
    """Create a new game and return the game ID."""
    main_grid = [[0]*9]*9
    wallv_grid = [[0]*9]*8
    wallh_grid = [[0]*8]*9
    wallfills_grid = [[0]*8]*8
    game_id = randint(0, 10000)
    last_status = "Starting game."
    if requested_players == "two":
        while TwoPlayerGame.objects.filter(game_id=game_id):
            game_id = randint(0, 10000)
        main_grid[0][4] = 1
        main_grid[8][4] = 2
        TwoPlayerGame.objects.create(
            game_id=game_id,
            player1=users[0],
            player2=users[1],
            player1_walls=10,
            player2_walls=10,
            main_grid=json.dumps(main_grid),
            wallv_grid=json.dumps(wallv_grid),
            wallh_grid=json.dumps(wallh_grid),
            wallfills_grid=json.dumps(wallfills_grid),
            last_status=last_status,
            turn=users[0])
    if requested_players == "four":
        while FourPlayerGame.objects.filter(game_id=game_id):
            game_id = randint(0, 10000)
        main_grid[0][4] = 1
        main_grid[8][4] = 2
        main_grid[4][0] = 3
        main_grid[4][8] = 2
        FourPlayerGame.objects.create(
            game_id=game_id,
            player1=users[0],
            player2=users[1],
            player3=users[2],
            player4=users[3],
            player1_walls=5,
            player2_walls=5,
            player3_walls=5,
            player4_walls=5,
            main_grid=json.dumps(main_grid),
            wallv_grid=json.dumps(wallv_grid),
            wallh_grid=json.dumps(wallh_grid),
            wallfills_grid=json.dumps(wallfills_grid),
            last_status=last_status,
            turn=users[0])
    return game_id


def _do_move(game, main_grid, wallh_grid, wallv_grid, wallfills_grid, move):
    """Apply the game move."""
    pass

def play(game, requested_players, move):
    """Play a move."""
    # Get game data.
    main_grid = json.loads(game.main_grid)
    wallh_grid = json.loads(game.wallh_grid)
    wallv_grid = json.loads(game.wallv_grid)
    wallfills_grid = json.loads(game.wallfills_grid)

    # Check to see if the move is legal. Do it if so.
    if check_move(main_grid, wallh_grid, wallv_grid, wallfills_grid, move):
        return _do_move(game, main_grid, wallh_grid, wallv_grid, wallfills_grid, move)
    else:
        return "Your move is not legal."
