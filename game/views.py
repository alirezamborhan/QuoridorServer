import datetime
import json
from passlib.hash import pbkdf2_sha256

from django.shortcuts import render
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.base import SessionBase
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden

from game.models import User, Waiter, TwoPlayerGame, FourPlayerGame
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

    # Check to see if user exists.
#    if not User.objects.filter(username=post["username"].lower()):
#        return HttpResponseForbidden("No such user exists.")

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
    pass

    return HttpResponse("You are now logged in, %s." % user.name)


def logout(request):
    """Log out of the server."""
    # Check if user is logged in at all.
    if not request.session.has_key("username"):
        return HttpResponseForbidden("Error: You are not logged in.")

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

def _add_to_new_game(game_id, session_keys, encode, requested_players):
    for session_key in session_keys:
        the_session = Session.objects.get(session_key=session_key)
        session = the_session.get_decoded()
        if "requested_players" not in session:
            session["requested_players"] = requested_players
        session["game_id"] = game_id
        the_session.session_data = encode(session)
        the_session.save()

def _update_waitlist():
    """Deletes excessive data from the waitlist."""
    pass

def _check_and_begin(encode, requested_players=""):
    """Checks waitlist and starts a new game if there are enough players."""
    _update_waitlist()

    for players in ("two", "four"):
        waiters = Waiter.objects.filter(requested_players=players)
        if len(waiters) != {"four": 4, "two": 2}[players]:
            continue
        # Start a new game.
        users = []
        session_keys = []
        for w in waiters:
            users.append(w.user)
            session_keys.append(w.session_key)
        game_id = Play.new(users, players)
        _add_to_new_game(game_id, session_keys, encode, requested_players)
        # Empty the waitlist.
        waiters.delete()

def two_or_four(request):
    """Page to choose the number of players."""
    # Check permission.
    if not request.session.has_key("username"):
        return HttpResponseForbidden("Error: You are not logged in.")

    # Check data validity.
    if request.method != "POST":
        return HttpResponseBadRequest("Error: Send your data via POST.")
    post = request.POST.dict()
    if (set(post.keys()) != {"players"}
        or (post["players"] != "two" and post["players"] != "four")
):
        return HttpResponseBadRequest("Error: Your POST data is corrupted.")

    # Add information to session.
    request.session["requested_players"] = post["players"]

    # Add to waitlist.
    Waiter.objects.create(user=User.objects.get(username=request.session["username"]),
                          session_key=request.session.session_key,
                          requested_players=post["players"])

#    _check_and_begin(request.session.encode, requested_players=post["players"])
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

    # Check to see if number of players is decided.
    if not request.session.has_key("requested_players"):
        return HttpResponseBadRequest(
            json.dumps({"error": "You have not chosen the number of players."}))

    # Check to see if game has started.
    if not request.session.has_key("game_id"):
        _check_and_begin(request.session.encode)
        return HttpResponse(
            json.dumps({"status": "Waiting for other players to join...",
                        "waiting": True}))
    
    # Get the game.
    if request.session["requested_players"] == "two":
        game = TwoPlayerGame.objects.get(game_id=request.session["game_id"])
    if request.session["requested_players"] == "four":
        game = FourPlayerGame.objects.get(game_id=request.session["game_id"])

    # Check turn.
    if game.turn.username != request.session["username"]:
        return HttpResponse(game.last_status + "\n"
                + game.main_grid + "\n" + game.wallh_grid + "\n"
                + game.wallv_grid + "\n" + game.wallfills_grid)

    # Check to see if any move has been made.
    if request.method != "POST":
        return HttpResponse(game.last_status + "\n"
                + game.main_grid + "\n" + game.wallh_grid + "\n"
                + game.wallv_grid + "\n" + game.wallfills_grid)
    post = request.POST.dict()

    # Check data validity.
    if (set(post.keys()) != {"move"} 
        or not _is_move_format_valid(json.loads(post["move"]))
):
        return HttpResponseBadRequest(
            json.dumps({"error": "Your POST data is corrupted."}))

    # Play the move.
    return Play.play(game,
                     request.session["requested_players"],
                     json.loads(post["move"]))
