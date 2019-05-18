from django.contrib.auth.models import User, Group
from .models import Card, Deck, Deck_Detail, Card_Vector_Point
from rest_framework import serializers


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')
    
    def create(self, validated_data):
        return User.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.url = validated_data.get('url', instance.url)
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('emailgroups', instance.emailgroups)
        instance.groups = validated_data.get('groups', instance.groups)
        instance.save()
        return instance


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')

    def create(self, validated_data):
        return Group.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.url = validated_data.get('url', instance.url)
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        return instance

class CardSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Card
        fields = ('id', 'multiverse_id', 'name', 'card_type', 'rarity', \
            'toughness', 'power', 'cmc', 'text_vector_1', 'text_vector_2', \
            'color_identity')

    def create(self, validated_data):
        return Card.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.multiverse_id = validated_data.get('multiverse_id', instance.multiverse_id)
        instance.name = validated_data.get('name', instance.name)
        instance.card_type = validated_data.get('card_type', instance.card_type)
        instance.toughness = validated_data.get('toughness', instance.toughness)
        instance.power = validated_data.get('power', instance.power)
        instance.rarity = validated_data.get('rarity', instance.rarity)
        instance.cmc = validated_data.get('cmc', instance.cmc)
        instance.color_identity = validated_data.get('color_identity', instance.color_identity)
        instance.save()
        return instance

class DeckSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Deck
        fields = ('id', 'deck_size', 'unique_count', 'name', 'url')
    
    def create(self, validated_data):
        return Deck.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.deck_size = validated_data.get('deck_size', instance.deck_size)
        instance.unique_count = validated_data.get('unique_count', instance.unique_count)
        instance.name = validated_data.get('name', instance.name)
        instance.url = validated_data.get('url', instance.url)
        instance.save()
        return instance

class DeckDetailSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Deck_Detail
        fields = ('card_id', 'deck_id', 'count', 'significance')
    
    def create(self, validated_data):
        return Deck_Detail.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.card_id = validated_data.get('card_id', instance.card_id)
        instance.deck_id = validated_data.get('deck_id', instance.deck_id)
        instance.count = validated_data.get('count', instance.count)
        instance.significance = validated_data.get('significance', instance.significance)
        instance.save()
        return instance

class CardVectorPointSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Card_Vector_Point
        fields = ('card_id', 'x_value', 'y_value', 'algorithm', 'alg_weight')
    
    def create(self, validated_data):
        return Card_Vector_Point.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.card_id = validated_data.get('card_name', instance.card_name)
        instance.x_value = validated_data.get('x_value', instance.x_value)
        instance.y_value = validated_data.get('y_value', instance.y_value)
        instance.algorithm = validated_data.get('algorithm', instance.algorithm)
        instance.alg_weight = validated_data.get('alg_weight', instance.alg_weight)
        instance.save()
        return instance