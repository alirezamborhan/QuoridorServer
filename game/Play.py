"""This module includes server-side functions needed to play Quoridor."""

import json
from random import randint

from django.contrib.sessions.models import Session
from game.models import TwoPlayerGame, FourPlayerGame, User
from django.http import HttpResponse, HttpResponseNotAllowed

from game.CheckMove import check_move, check_win


def get_game(username):
    """Get the game the user is playing.
Return None if they're not in any game.
"""
    user = User.objects.get(username=username)
    if user.two_player_game_id != None:
        return TwoPlayerGame.objects.get(
            game_id=user.two_player_game_id), "two"
    if user.four_player_game_id != None:
        return FourPlayerGame.objects.get(
            game_id=user.four_player_game_id), "four"
    return None, None

def new(user, requested_players):
    """Create a new game and return the game ID."""
    main_grid = [[0]*9 for _ in range(9)]
    wallv_grid = [[0]*8 for _ in range(9)]
    wallh_grid = [[0]*9 for _ in range(8)]
    wallfills_grid = [[0]*8 for _ in range(8)]
    game_id = randint(0, 1000000)
    last_status = json.dumps({"status": "Waiting for other players to join...",
                              "waiting": True})
    if requested_players == "two":
#        while TwoPlayerGame.objects.filter(game_id=game_id):
#            game_id = randint(0, 10000)
        user.two_player_game_id = game_id
        main_grid[0][4] = 1
        main_grid[8][4] = 2
        TwoPlayerGame.objects.create(
            game_id=game_id,
            player1=user,
            player1_walls=10,
            player2_walls=10,
            main_grid=json.dumps(main_grid),
            wallv_grid=json.dumps(wallv_grid),
            wallh_grid=json.dumps(wallh_grid),
            wallfills_grid=json.dumps(wallfills_grid),
            last_status=last_status,
            turn=user)
    if requested_players == "four":
#        while FourPlayerGame.objects.filter(game_id=game_id):
#            game_id = randint(0, 10000)
        user.four_player_game_id = game_id
        main_grid[0][4] = 1
        main_grid[8][4] = 2
        main_grid[4][0] = 3
        main_grid[4][8] = 4
        FourPlayerGame.objects.create(
            game_id=game_id,
            player1=user,
            player1_walls=5,
            player2_walls=5,
            player3_walls=5,
            player4_walls=5,
            main_grid=json.dumps(main_grid),
            wallv_grid=json.dumps(wallv_grid),
            wallh_grid=json.dumps(wallh_grid),
            wallfills_grid=json.dumps(wallfills_grid),
            last_status=last_status,
            turn=user)
    user.save()
    return


def get_walls(game, requested_players):
    walls = dict()
    walls["1"] = [game.player1.username, game.player1_walls]
    walls["2"] = [game.player2.username, game.player2_walls]
    if requested_players == "four":
        walls["3"] = [game.player3.username, game.player3_walls]
        walls["4"] = [game.player4.username, game.player4_walls]
    return json.dumps(walls)

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
        if player == 1:
            game.player1_walls -= 1
        elif player == 2:
            game.player2_walls -= 1
        elif player == 3:
            game.player3_walls -= 1
        elif player == 4:
            game.player4_walls -= 1

    if move["type"] == "wall" and move["direction"] == "v":
        wallv_grid[y][x] = 1
        wallv_grid[y+1][x] = 1
        wallfills_grid[y][x] = 1
        if player == 1:
            game.player1_walls -= 1
        elif player == 2:
            game.player2_walls -= 1
        elif player == 3:
            game.player3_walls -= 1
        elif player == 4:
            game.player4_walls -= 1

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

    # Check to see if the game has been won. Apply scores if so.
    if check_win(main_grid, player):
        if requested_players == "two":
            players = {1: game.player1, 2: game.player2}
            winner = players[player]
            winner.two_player_wins += 1
            winner.total_score += 1
            winner.save()
            for p in players.values():
                if p == winner:
                    continue
                p.two_player_losses += 1
                p.total_score -= 1
                p.save()
        if requested_players == "four":
            players = {1: game.player1, 2: game.player2,
                      3: game.player3, 4: game.player4}
            winner = players[player]
            winner.four_player_wins += 1
            winner.total_score += 3
            winner.save()
            for p in players.values():
                if p == winner:
                    continue
                p.four_player_losses += 1
                p.total_score -= 1
                p.save()
        last_status = json.dumps({"winner": winner.username,
                                  "status": "%s has won the game!"
                                  % winner.username.capitalize()})
    
    # Update database.
    game.last_status = last_status
    game.main_grid = json.dumps(main_grid)
    game.wallh_grid = json.dumps(wallh_grid)
    game.wallv_grid = json.dumps(wallv_grid)
    game.wallfills_grid = json.dumps(wallfills_grid)
    game.save()

    return (last_status + "\n" + game.main_grid + "\n" + game.wallh_grid
            + "\n" + game.wallv_grid + "\n" + game.wallfills_grid
            + "\n" + get_walls(game, requested_players))

def play(game, requested_players, move):
    """Play a move."""
    # Extract game data.
    main_grid = json.loads(game.main_grid)
    wallh_grid = json.loads(game.wallh_grid)
    wallv_grid = json.loads(game.wallv_grid)
    wallfills_grid = json.loads(game.wallfills_grid)
    if requested_players == "two":
        walls = {1: game.player1_walls, 2: game.player2_walls}
    if requested_players == "four":
        walls = {1: game.player1_walls, 2: game.player2_walls,
                 3: game.player3_walls, 4: game.player4_walls}
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
                  wallfills_grid, move, player, walls):
        response = _do_move(game, main_grid, wallh_grid, wallv_grid,
                        wallfills_grid, move, player, requested_players)
        return HttpResponse(response)
    else:
        response = json.dumps({"error": "illegal move",
                               "turn": game.turn.username})
        response += ("\n" + game.main_grid + "\n" + game.wallh_grid
                     + "\n" + game.wallv_grid + "\n" + game.wallfills_grid
                     + "\n" + get_walls(game, requested_players))
        return HttpResponse(response)

def stop(game, requested_players, username, already_stopped=False):
    """Function to stop and leave the game.
If the game has already been stopped, remove
the player from the game.
"""
    user = User.objects.get(username=username)
    user.two_player_game_id = None
    user.four_player_game_id = None
    user.save()
    if game.player1 == user:
        game.player1 = None
    elif game.player2 == user:
        game.player2 = None
    elif game.player3 == user:
        game.player3 = None
    elif game.player4 == user:
        game.player4 = None
    if not already_stopped:
        game.turn = None
        game.last_status = json.dumps({"stopped": True,
                                "status": ("The game has been stopped by %s"
                                                % username)})
    last_status = game.last_status
    if ((requested_players == "two" and game.player1 == None and
         game.player2 == None) or
        (requested_players == "four" and game.player1 == None and
         game.player2 == None and game.player3 == None and
         game.player4 == None)):
            game.delete()
    else:
        game.save()
    return HttpResponse(last_status)
