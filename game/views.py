import datetime
from passlib.hash import pbkdf2_sha256

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden

from game.models import User, Waiter, TwoPlayerGame, FourPlayerGame


def is_username_valid(username):
    """Check to see if username is valid."""
    if (3 <= len(username) <= 100
        and username.replace('_', '').isalnum()
        and (username[0].isalpha() or username[0] == '_')
):
        return True
    return False

def is_password_valid(password):
    """Check to see if password is valid."""
    if len(password) >= 8:
        return True
    return False

def is_name_valid(name):
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
        or not is_name_valid(post["name"])
        or not is_username_valid(post["username"].lower())
        or not is_password_valid(post["password"])
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
    if request.method != "POST":
        return HttpResponseBadRequest("Error: Send your data via POST.")
    post = request.POST.dict()
    
    # Check data validity.
    if (set(post.keys()) != {"name", "username", "password"} 
        or not is_name_valid(post["name"])
        or not is_username_valid(post["username"].lower())
        or not is_password_valid(post["password"])
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
    pass

    return HttpResponse("You are now logged in, %s." % user.name)


def check_waitlist(players):
    """Checks to see if there are enough players
to start a game. Empties the waitlist afterwards.
"""
    waiters = Waiter.objects.filter(requested_players=players)
    if len(waiters) == {"four": 4, "two": 2}[players]:
        return True
    return False

def two_or_four(request):
    """Function to choose the number of players."""
    if request.method != "POST":
        return HttpResponseBadRequest("Error: Send your data via POST.")
    post = request.POST.dict()

    # Check permission.
    if not request.session.has_key("username"):
        return HttpResponseForbidden("Error: You are not logged in.")

    # Check data validity.
    if (set(post.keys()) != {"players"}
        or (post["players"] != "two" and post["players"] != "four")
):
        return HttpResponseBadRequest("Error: Your POST data is corrupted.")

    session["requested_players"] = post["players"]
    Waiter.objects.create(user=User.objects.get(username=session["username"]),
                          requested_players=post["players"])
    if check_waitlist(post["players"]):
        # Start a game
        pass
