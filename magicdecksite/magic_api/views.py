from django.contrib.auth.models import User, Group
from .models import Card, Deck, Deck_Detail
from .serializers import *
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

class CardViewSet(viewsets.ModelViewSet):
    queryset = Card.objects.all()
    serializer_class = CardSerializer

@api_view(['GET', 'POST', 'PUT'])
@permission_classes((permissions.AllowAny,))
def card_list(request):
    if request.method == 'GET':
        cards = Card.objects.all()
        serializer = CardSerializer(cards, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = CardSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'PUT':
        req_name = request.data['name']
        try:
            card = Card.objects.filter(name=req_name)[:1].get()
            serializer = CardSerializer(card, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except:
            serializer = CardSerializer(data=request.data)
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
        serializer = CardSerializer(card)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = CardSerializer(card, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        card.delete()
        return Response(status=status.HTTP_204_NO_CONTENT) 

class DeckViewSet(viewsets.ModelViewSet):
    queryset = Deck.objects.all()
    serializer_class = DeckSerializer

@api_view(['GET', 'POST'])
@permission_classes((permissions.AllowAny,))
def deck_list(request):
    if request.method == 'GET':
        decks = Deck.objects.all()
        serializer = DeckSerializer(decks, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = DeckSerializer(data=request.data)
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
        serializer = DeckSerializer(deck)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = DeckSerializer(deck, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        deck.delete()
        return Response(status=status.HTTP_204_NO_CONTENT) 

class DeckDetailViewSet(viewsets.ModelViewSet):
    queryset = Deck_Detail.objects.all()
    serializer_class = DeckDetailSerializer

@api_view(['GET', 'POST'])
@permission_classes((permissions.AllowAny,))
def deck_detail_list(request):
    if request.method == 'GET':
        deck_details = Deck_Detail.objects.all()
        serializer = DeckDetailSerializer(deck_details, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = DeckDetailSerializer(data=request.data)
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
        serializer = DeckDetailSerializer(deck_detail)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = DeckDetailSerializer(deck_detail, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        deck_detail.delete()
        return Response(status=status.HTTP_204_NO_CONTENT) 

class CardVectorViewSet(viewsets.ModelViewSet):
    queryset = Card_Vector_Point.objects.all()
    serializer_class = CardVectorPointSerializer

@api_view(['GET', 'POST', 'PUT'])
@permission_classes((permissions.AllowAny,))
def card_vector_list(request):
    if request.method == 'GET':
        card_vectors = Card_Vector_Point.objects.all()
        serializer = CardVectorPointSerializer(card_vectors, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = CardVectorPointSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        req_id = request.data['card']
        req_alg = request.data['algorithm']
        req_weight = request.data['alg_weight']
        try:
            point = Card_Vector_Point.objects.filter(card=req_id, algorithm=req_alg, \
                 alg_weight=req_weight)[:1].get()
            serializer = CardVectorPointSerializer(point, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except:
            serializer = CardVectorPointSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes((permissions.AllowAny,))
def card_vector_info(request, pk):
    try:
        card_vector = Card_Vector_Point.objects.get(pk=pk)
    except Deck_Detail.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = CardVectorPointSerializer(card_vector)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = CardVectorPointSerializer(card_vector, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        card_vector.delete()
        return Response(status=status.HTTP_204_NO_CONTENT) 
