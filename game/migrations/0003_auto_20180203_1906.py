# Generated by Django 2.0 on 2018-02-03 19:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0002_waiter_session_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='twoplayergame',
            name='started',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='four_player_game_id',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='two_player_game_id',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='fourplayergame',
            name='player3',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='third_player', to='game.User'),
        ),
        migrations.AlterField(
            model_name='fourplayergame',
            name='player4',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fourth_player', to='game.User'),
        ),
        migrations.AlterField(
            model_name='twoplayergame',
            name='player1',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='first_player', to='game.User'),
        ),
        migrations.AlterField(
            model_name='twoplayergame',
            name='player2',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='second_player', to='game.User'),
        ),
    ]
