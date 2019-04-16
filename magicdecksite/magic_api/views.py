from django.contrib.auth.models import User, Group
from magic_api.models import Card, Deck, Deck_Detail
import magic_api.serializers as serial
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = serial.UserSerializer

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = serial.GroupSerializer

class CardViewSet(viewsets.ModelViewSet):
    queryset = Card.objects.all()
    serializer_class = serial.CardSerializer

@api_view(['GET', 'POST'])
@permission_classes((permissions.AllowAny,))
def card_list(request):
    if request.method == 'GET':
        cards = Card.objects.all()
        serializer = serial.CardSerializer(cards, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = serial.CardSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes((permissions.AllowAny,))
def card_detail(request, pk):
    try:
        card = Card.objects.get(pk=pk)
    except Card.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = serial.CardSerializer(card)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = serial.CardSerializer(card, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        card.delete()
        return Response(status=status.HTTP_204_NO_CONTENT) 

class DeckViewSet(viewsets.ModelViewSet):
    queryset = Deck.objects.all()
    serializer_class = serial.DeckSerializer

@api_view(['GET', 'POST'])
@permission_classes((permissions.AllowAny,))
def deck_list(request):
    if request.method == 'GET':
        decks = Deck.objects.all()
        serializer = serial.DeckSerializer(decks, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = serial.DeckSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes((permissions.AllowAny,))
def deck_info(request, pk):
    try:
        deck = Deck.objects.get(pk=pk)
    except Deck.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = serial.DeckSerializer(deck)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = serial.DeckSerializer(deck, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        deck.delete()
        return Response(status=status.HTTP_204_NO_CONTENT) 

class DeckDetailViewSet(viewsets.ModelViewSet):
    queryset = Deck_Detail.objects.all()
    serializer_class = serial.DeckDetailSerializer

@api_view(['GET', 'POST'])
@permission_classes((permissions.AllowAny,))
def deck_detail_list(request):
    if request.method == 'GET':
        deck_details = Deck_Detail.objects.all()
        serializer = serial.DeckDetailSerializer(deck_details, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = serial.DeckDetailSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes((permissions.AllowAny,))
def deck_detail_info(request, pk):
    try:
        deck_detail = Deck_Detail.objects.get(pk=pk)
    except Deck_Detail.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = serial.DeckDetailSerializer(deck_detail)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = serial.DeckDetailSerializer(deck_detail, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        deck_detail.delete()
        return Response(status=status.HTTP_204_NO_CONTENT) 