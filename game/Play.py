"""This module includes server-side functions needed to play Quoridor."""

import json
from random import randint

from django.contrib.sessions.models import Session
from game.models import TwoPlayerGame, FourPlayerGame
from django.http import HttpResponse, HttpResponseNotAllowed

from game.CheckMove import check_move


def new(users, requested_players):
    """Create a new game and return the game ID."""
    main_grid = [[0]*9 for _ in range(9)]
    wallv_grid = [[0]*8 for _ in range(9)]
    wallh_grid = [[0]*9 for _ in range(8)]
    wallfills_grid = [[0]*8 for _ in range(8)]
    game_id = randint(0, 1000000)
    last_status = json.dumps({"status": "Starting game.",
                              "turn": users[0].username,
                              "new": True})
    if requested_players == "two":
#        while TwoPlayerGame.objects.filter(game_id=game_id):
#            game_id = randint(0, 10000)
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
#        while FourPlayerGame.objects.filter(game_id=game_id):
#            game_id = randint(0, 10000)
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


def _do_move(game, main_grid, wallh_grid, wallv_grid,
             wallfills_grid, move, player, requested_players):
    """Apply the game move."""
    # Extract destination coordinations.
    x = move["x"]
    y = move["y"]

    if move["type"] == "move":
        for i in range(len(main_grid)):
            if player in main_grid[i]:
                py = i
                px = main_grid[i].index(player)
        main_grid[y][x] = player
        main_grid[py][px] = 0

    if move["type"] == "wall" and move["direction"] == "h":
        wallh_grid[y][x] = 1
        wallh_grid[y][x+1] = 1
        wallfills_grid[y][x] = 1

    if move["type"] == "wall" and move["direction"] == "v":
        wallv_grid[y][x] = 1
        wallv_grid[y+1][x] = 1
        wallfills_grid[y][x] = 1

    if requested_players == "two":
        if player == 1:
            game.turn = game.player2
        if player == 2:
            game.turn = game.player1
    if requested_players == "four":
        if player == 1:
            game.turn = game.player2
        if player == 2:
            game.turn = game.player3
        if player == 3:
            game.turn = game.player4
        if player == 4:
            game.turn = game.player1

    last_status = json.dumps({"status": "playing", "turn": game.turn.username})
    
    # Update database.
    game.last_status = last_status
    game.main_grid = json.dumps(main_grid)
    game.wallh_grid = json.dumps(wallh_grid)
    game.wallv_grid = json.dumps(wallv_grid)
    game.wallfills_grid = json.dumps(wallfills_grid)
    game.save()

    return (last_status + "\n" + game.main_grid + "\n" + game.wallh_grid
            + "\n" + game.wallv_grid + "\n" + game.wallfills_grid)

def play(game, requested_players, move):
    """Play a move."""
    # Get game data.
    main_grid = json.loads(game.main_grid)
    wallh_grid = json.loads(game.wallh_grid)
    wallv_grid = json.loads(game.wallv_grid)
    wallfills_grid = json.loads(game.wallfills_grid)
    if game.turn == game.player1:
        player = 1
    if game.turn == game.player2:
        player = 2
    if requested_players == "four":
        if game.turn == game.player3:
            player = 3
        if game.turn == game.player4:
            player = 4

    # Check to see if the move is legal. Do it if so.
    if check_move(main_grid, wallh_grid, wallv_grid,
                  wallfills_grid, move, player):
        response = _do_move(game, main_grid, wallh_grid, wallv_grid,
                        wallfills_grid, move, player, requested_players)
        return HttpResponse(response)
    else:
        response = json.dumps({"error": "illegal move",
                               "turn": game.turn.username})
        response += ("\n" + game.main_grid + "\n" + game.wallh_grid
                     + "\n" + game.wallv_grid + "\n" + game.wallfills_grid)
        return HttpResponse(response)
