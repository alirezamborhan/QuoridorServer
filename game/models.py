from django.db import models


class User(models.Model):
    name = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    password_hash = models.CharField(max_length=100)
    date_registered = models.DateTimeField()
    two_player_wins = models.IntegerField()
    two_player_losses = models.IntegerField()
    four_player_wins = models.IntegerField()
    four_player_losses = models.IntegerField()
    total_score = models.IntegerField()

class Waiter(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    requested_players = models.CharField(max_length=4)

class TwoPlayerGame(models.Model):
    game_id = models.IntegerField(primary_key=True)
    player1 = models.OneToOneField(User, on_delete=models.CASCADE)
    player2 = models.OneToOneField(User, on_delete=models.CASCADE)
    player1_walls = models.IntegerField()
    player2_walls = models.IntegerField()
    main_grid = models.CharField(max_length=270)
    wallh_grid = models.CharField(max_length=240)
    wallv_grid = models.CharField(max_length=240)
    wallfills_grid = models.CharField(max_length=210)
    last_status = models.CharField(max_length=500)
    turn = models.OneToOneField(User, on_delete=models.CASCADE)

class FourPlayerGame(TwoPlayerGame):
    player3 = models.OneToOneField(User, on_delete=models.CASCADE)
    player4 = models.OneToOneField(User, on_delete=models.CASCADE)
    player3_walls = models.IntegerField()
    player4_walls = models.IntegerField()
