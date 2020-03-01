from django.db import models

class Deck(models.Model):
    id = models.AutoField(primary_key=True)
    deck_size = models.BigIntegerField(default=0)
    unique_count = models.BigIntegerField(default=0)
    name = models.CharField(max_length=200)
    url = models.CharField(max_length=200, unique=True)

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return self.name + ": " + self.deck_size


class Card(models.Model):
    id = models.AutoField(primary_key=True)
    multiverse_id = models.BigIntegerField(default=0)
    name = models.CharField(max_length=200, unique=True)
    rarity = models.IntegerField(
        default=0,
        choices=((0, 'common'), (1, 'uncommon'), (2, 'rare'), (3, 'mythic')))
    card_type = models.FloatField(default=0)
    toughness = models.CharField(max_length=200)
    power = models.CharField(max_length=200)
    cmc = models.BigIntegerField(default=0)
    color_identity = models.IntegerField(
        default=0,
        choices=((0, 'C'), (1, 'R'), (2, 'U'), (3, 'G'), \
        (4, 'B'), (5, 'W'), (6, 'RU'), (7, 'RG'), (8, 'RB'), \
        (9, 'RW'), (10, 'UG'), (11, 'UB'), (12, 'UW'), (13, 'GB'), \
        (14, 'GW'), (15, 'BW'), (16, 'RUG'), (17, 'RUB'), \
        (18, 'RUW'), (19, 'RGB'), (20, 'RGW'), (21, 'RBW'), \
        (22, 'UGB'), (23, 'UGW'), (24, 'UBW'), (25, 'GBW'), \
        (26, 'RUGB'), (27, 'RUGW'), (28, 'RUBW'), (29, 'RGBW'), \
        (30, 'UGBW'), (31, 'RUGBW')))

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return self.name + " - " + str(self.multiverse_id) + ": " + str(self.card_type)

class Card_Vector_Point(models.Model):
    id = models.AutoField(primary_key=True)
    card = models.ForeignKey(Card, to_field='name', on_delete=models.CASCADE)
    x_value = models.FloatField(default=0)
    y_value = models.FloatField(default=0)
    algorithm = models.CharField(max_length=200)
    alg_weight = models.BigIntegerField(default=0)

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return self.card_name + " : " + self.algorithm + alg_weight + " - x: " + \
            self.x_value + ", y: " + self.y_value

class Deck_Detail(models.Model):
    id = models.AutoField(primary_key=True)
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    count = models.BigIntegerField(default=0)
    significance = models.FloatField(default=0)

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return self.deck_id + " - " + self.card_id
