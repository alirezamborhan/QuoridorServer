import datetime
import json
from passlib.hash import pbkdf2_sha256

from django.shortcuts import render
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.base import SessionBase
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden

from game.models import User, TwoPlayerGame, FourPlayerGame
import game.Play as Play


def _is_username_valid(username):
    """Check to see if username is valid."""
    if (3 <= len(username) <= 100
        and username.replace('_', '').isalnum()
        and (username[0].isalpha() or username[0] == '_')
):
        return True
    return False

def _is_password_valid(password):
    """Check to see if password is valid."""
    if len(password) >= 8:
        return True
    return False

def _is_name_valid(name):
    """Check to see if name is valid."""
    if 0 <= len(name) <= 100:
        return True
    return False


def signup(request):
    """Sign up in the server"""
    if request.method != "POST":
        return HttpResponseBadRequest("Error: Send your data via POST.")
    post = request.POST.dict()
    
    # Check data validity.
    if (set(post.keys()) != {"name", "username", "password"} 
        or not _is_name_valid(post["name"])
        or not _is_username_valid(post["username"].lower())
        or not _is_password_valid(post["password"])
):
        return HttpResponseBadRequest("Error: Your POST data is corrupted.")
    
    # Check if user already exists.
    if User.objects.filter(username=post["username"].lower()):
        return HttpResponseBadRequest("This user already exists.")

    # Hash password.
    password_hash = pbkdf2_sha256.encrypt(post["password"],
                                          rounds=100000,
                                          salt_size=16)

    # Register.
    date = datetime.datetime.now()
    User.objects.create(name=post['name'],
                        username=post['username'].lower(),
                        password_hash=password_hash,
                        date_registered=date,
                        two_player_wins=0,
                        two_player_losses=0,
                        four_player_wins=0,
                        four_player_losses=0,
                        total_score=0)
    return HttpResponse("Registration has been completed.")


def signin(request):
    """Sign into the server."""
    # Check to see if user is already logged in.
    if request.session.has_key("username"):
        return HttpResponseBadRequest("Error: You are already logged in.")

    if request.method != "POST":
        return HttpResponseBadRequest("Error: Send your data via POST.")
    post = request.POST.dict()
    
    # Check data validity.
    if (set(post.keys()) != {"username", "password"}
        or not _is_username_valid(post["username"].lower())
        or not _is_password_valid(post["password"])
):
        return HttpResponseBadRequest("Error: Your POST data is corrupted.")

    # Get user from database.
    try:
        user = User.objects.get(username=post["username"].lower())
    except User.DoesNotExist:
        return HttpResponseForbidden("No such user exists.")

    # Verify password hash.
    if not pbkdf2_sha256.verify(post["password"], user.password_hash):
        return HttpResponseForbidden("Your password is incorrect.")

    # Set up session.
    request.session["username"] = user.username

    # Check to see if the user is already in a game.
    (game, requested_players) = Play.get_game(request.session["username"])
    if game:
        return HttpResponse("You're already in a game.")

    return HttpResponse("You are now logged in, %s." % user.name)


def logout(request):
    """Log out of the server."""
    # Check if user is logged in at all.
    if not request.session.has_key("username"):
        return HttpResponse("Error: You are not logged in.")

    # Clear session.
    request.session.clear()
    return HttpResponse("You have logged out.")


def _check_waitlist(players):
    """Checks to see if there are enough players
to start a game. Empties the waitlist afterwards.
"""
    waiters = Waiter.objects.filter(requested_players=players)
    if len(waiters) == {"four": 4, "two": 2}[players]:
        return True
    return False

def _add_to_game(username, requested_players):
    """Add user to a game that is not started, or create a new game."""
    user = User.objects.get(username=username)
    
    # Get game.
    if (requested_players == "two"
          and TwoPlayerGame.objects.filter(started=False)):
        game = TwoPlayerGame.objects.get(started=False)
        user.two_player_game_id = game.game_id
    elif (requested_players == "four"
          and FourPlayerGame.objects.filter(started=False)):
        game = FourPlayerGame.objects.get(started=False)
        user.four_player_game_id = game.game_id
    else:
        # If there is no unstarted game.
        Play.new(user, requested_players)
        return

    # Add the user.
    if not game.player1:
        game.player1 = user
    elif not game.player2:
        game.player2 = user
    elif not game.player3:
        game.player3 = user
    elif not game.player4:
        game.player4 = user

    if not game.turn:
        game.turn = user

    # Check to see if there are enough players to start.
    # Start if so.
    if requested_players == "two":
        if (game.player1 and game.player2):
            game.started = True
            game.last_status = json.dumps({"status": "Starting game.",
                              "turn": game.turn.username,
                              "new": True})
    if requested_players == "four":
        if (game.player1 and game.player2
              and game.player3 and game.player4):
            game.started = True
            game.last_status = json.dumps({"status": "Starting game.",
                              "turn": game.turn.username,
                              "new": True})
            
    game.save()
    user.save()


def two_or_four(request):
    """Page to choose the number of players."""
    # Check permission.
    if not request.session.has_key("username"):
        return HttpResponseForbidden("Error: You are not logged in.")

    # Check to see if the user is already in a game.
    (game, requested_players) = Play.get_game(request.session["username"])
    if game:
        return HttpResponseBadRequest("Error: You're already in a game.")

    # Check data validity.
    if request.method != "POST":
        return HttpResponseBadRequest("Error: Send your data via POST.")
    post = request.POST.dict()
    if (set(post.keys()) != {"players"}
        or (post["players"] != "two" and post["players"] != "four")
):
        return HttpResponseBadRequest("Error: Your POST data is corrupted.")

    # Add user to a new game.
    _add_to_game(request.session["username"], post["players"])

    return HttpResponse("You've been added to the waitlist.")


def _is_move_format_valid(move):
    """Checks the format for the received data for a game move.
A proper datum would be a dictionary similar to:
{"type": "move", "x": 1, "y": 4}
Which would move the player to the cell at (1, 4).
Or it could be a dictionary similar to:
{"type": "wall", "direction": "h", "x": 7, "y": 3}
Which would place a horizontal wall with the northwest corner at (7, 3).
Or it could be a dictionary similar to:
{"type": "wall", "direction": "v", "x": 6, "y": 3}
Which would place a vertical wall with the northwest corner at (6, 3).
"""
    if (not isinstance(move, dict)
        or not (set(move.keys()) == {"type", "x", "y"}
                or set(move.keys()) == {"type", "direction", "x", "y"}
)):
          return False
    if (move["type"] == "move"
        and len(move) == 3
        and isinstance(move["x"], int)
        and isinstance(move["y"], int)
        and 0 <= move["x"] <= 8
        and 0 <= move["y"] <= 8
):
          return True
    if (move["type"] == "wall"
        and len(move) == 4
        and isinstance(move["x"], int)
        and isinstance(move["y"], int)
        and (move["direction"] == "h"
             or move["direction"] == "v")
        and 0 <= move["x"] <= 7
        and 0 <= move["y"] <= 7
):
          return True
    return False

def play_and_status(request):
    """Play moves if game has started.
If not, check waitlist and start a new game.
"""
    # Check permission.
    if not request.session.has_key("username"):
        return HttpResponseForbidden(
            json.dumps({"error": "You are not logged in."}))

    # Check to see if game has been chosen.
    (game, requested_players) = Play.get_game(request.session["username"])
    if not game:
        return HttpResponseBadRequest(
            json.dumps({"error": "You have not chosen a game."}))

    # Check to see if game has started.
    if not game.started:
        return HttpResponse(game.last_status)

    # Check to see if the game has been won by someone.
    if "winner" in json.loads(game.last_status):
        response = HttpResponse(game.last_status + "\n"
                + game.main_grid + "\n" + game.wallh_grid + "\n"
                + game.wallv_grid + "\n" + game.wallfills_grid
                                + "\n" + json.dumps(dict()))
        Play.stop(game, requested_players,
                  request.session["username"],
                  already_stopped=True)
        return response

    if "stopped" in json.loads(game.last_status):
        response = Play.stop(game, requested_players,
                             request.session["username"],
                             already_stopped=True)
        return response

    # Check turn.
    if game.turn.username != request.session["username"]:
        return HttpResponse(game.last_status + "\n"
                + game.main_grid + "\n" + game.wallh_grid + "\n"
                + game.wallv_grid + "\n" + game.wallfills_grid
               + "\n" + Play.get_walls(game, requested_players))

    # Check to see if any move has been made.
    if request.method != "POST":
        return HttpResponse(game.last_status + "\n"
                + game.main_grid + "\n" + game.wallh_grid + "\n"
                + game.wallv_grid + "\n" + game.wallfills_grid
               + "\n" + Play.get_walls(game, requested_players))
    post = request.POST.dict()

    # Check data validity.
    if (set(post.keys()) != {"move"} 
        or not _is_move_format_valid(json.loads(post["move"]))
):
        return HttpResponseBadRequest(
            json.dumps({"error": "Your POST data is corrupted."}))

    # Play the move.
    return Play.play(game,
                     requested_players,
                     json.loads(post["move"]))

def leave(request):
    """To stop and leave the game.
If one player chooses to leave the game, the whole game
will be stopped and other users will be notified.
"""
    # Check permission.
    if not request.session.has_key("username"):
        return HttpResponseForbidden(
            json.dumps({"error": "You are not logged in."}))

    # Check to see if game has been chosen.
    (game, requested_players) = Play.get_game(request.session["username"])
    if not game:
        return HttpResponseBadRequest(
            json.dumps({"error": "You have not chosen a game."}))

    # Stops the game.
    last_status = json.loads(game.last_status)
    already_stopped = ("winner" in last_status or "stopped" in last_status)
    response = Play.stop(game, requested_players, request.session["username"],
                            already_stopped=already_stopped)

    return response

def scores(request):
    """Give scores for all users."""
    # Check permission.
    if not request.session.has_key("username"):
        return HttpResponseForbidden(
            json.dumps({"error": "You are not logged in."}))

    # Get scores.
    response = ""
    users = User.objects.all()
    users_sorted = list(reversed(
        sorted([[user.total_score, user.username] for user in users])))
    rank = 0
    last_score = 0
    for i in range(len(users_sorted)):
        if last_score != users_sorted[i][0]:
            rank = i+1
            last_score = users_sorted[i][0]
        user_info = "\n%s %s %s" % (str(rank).ljust(5),
                                    users_sorted[i][1].ljust(14),
                                    str(users_sorted[i][0]).ljust(5))
        response += user_info
        if users_sorted[i][1] == request.session["username"]:
            response = user_info + "\n" + response
    first_line = "%s %s %s\n" % (("Rank").ljust(5),
                               ("Username").ljust(14),
                               ("Score").ljust(5))
    response += "\n"
    response = first_line + response
    return HttpResponse(response)

def user_info(request):
    """Give saved information about the user."""
    # Check permission.
    if not request.session.has_key("username"):
        return HttpResponseForbidden(
            json.dumps({"error": "You are not logged in."}))

    # Get user.
    user = User.objects.get(username=request.session["username"])

    # Create response.
    h1 = 17
    h2 = 12
    response = ""
    response += ("Username:").ljust(h1) + user.username.ljust(h2) + "\n"
    response += ("Name:").ljust(h1) + user.name.ljust(h2) + "\n"
    response += (("2 player wins:").ljust(h1)
                 + str(user.two_player_wins).ljust(h2) + "\n")
    response += (("2 player losses:").ljust(h1)
                 + str(user.two_player_losses).ljust(h2) + "\n")
    response += (("4 player wins:").ljust(h1)
                 + str(user.four_player_wins).ljust(h2) + "\n")
    response += (("2 player losses:").ljust(h1)
                 + str(user.four_player_losses).ljust(h2) + "\n")
    response += (("Total score:").ljust(h1)
                 + str(user.total_score).ljust(h2) + "\n")

    return HttpResponse(response)
