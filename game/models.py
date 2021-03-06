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
    two_player_game_id = models.IntegerField(null=True, blank=True)
    four_player_game_id = models.IntegerField(null=True, blank=True)
    def __str__(self):
        return self.username

class TwoPlayerGame(models.Model):
    game_id = models.IntegerField(primary_key=True)
    player1 = models.OneToOneField(User, on_delete=models.CASCADE,
                                   related_name="first_player",
                                   null=True, blank=True)
    player2 = models.OneToOneField(User, on_delete=models.CASCADE,
                                   related_name="second_player",
                                   null=True, blank=True)
    player1_walls = models.IntegerField()
    player2_walls = models.IntegerField()
    main_grid = models.CharField(max_length=270)
    wallh_grid = models.CharField(max_length=240)
    wallv_grid = models.CharField(max_length=240)
    wallfills_grid = models.CharField(max_length=210)
    last_status = models.CharField(max_length=500)
    turn = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name="turn_player",
                                null=True, blank=True)
    started = models.BooleanField(default=False)
    def __str__(self):
        return str(self.game_id)

class FourPlayerGame(TwoPlayerGame):
    player3 = models.OneToOneField(User, on_delete=models.CASCADE,
                                   related_name="third_player",
                                   null=True, blank=True)
    player4 = models.OneToOneField(User, on_delete=models.CASCADE,
                                   related_name="fourth_player",
                                   null=True, blank=True)
    player3_walls = models.IntegerField()
    player4_walls = models.IntegerField()
