from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.db import IntegrityError, transaction
from django.contrib.auth import get_user_model
from events.models import Category, Event
from .models import Participation


class ParticipationSecurityTests(TestCase):
    def setUp(self):
        User = get_user_model()
        owner = User.objects.create_user(
            username='owner',
            email='owner@test.com',
            password='ownerpass123'
        )
        self.owner = owner

        participant = User.objects.create_user(
            username='participant',
            email='participant@test.com',
            password='testpass123'
        )
        self.participant = participant

        unauthorized = User.objects.create_user(
               username='outsider',
               email='outsider@test.com',
               password='unauthorizedpass123'
        )
        self.unauthorized = unauthorized

        category = Category.objects.create(
            name='Sports'
        )
        self.category = category

        event = Event.objects.create(
            title='Test Cricket Match',
            description='Testing participation security',
            category=self.category,
            created_by= self.owner,
            location='Pune',
            event_date=timezone.now(),
            max_participants=10
        )

        self.event = event

        participation = Participation.objects.create(
            user=self.participant,
            event=self.event,
            status='PENDING'
        )

        self.participation = participation

        pass

    def test_non_owner_cannot_accept_request(self):
        self.client.login(
            username=self.participant.username, 
            password='testpass123'
        )

        url = reverse(
            'accept_request', 
            args=[self.participation.id]
        )

        response = self.client.post(url)

        self.participation.refresh_from_db()

        self.assertEqual(
            self.participation.status, 
            "PENDING"
        )
            
        pass    

    def test_non_owner_cannot_reject_request(self):
       
       self.client.login(
           username=self.unauthorized.username, 
           password='unauthorizedpass123'
           )
       
       url = reverse(
           'reject_request', 
           args=[self.participation.id]
        )
       
       response = self.client.post(url)

       self.participation.refresh_from_db()

       self.assertEqual(
           self.participation.status, 
           "PENDING"
        )   

    def test_owner_can_accept_request(self):
        self.client.login(
            username=self.owner.username,
            password='ownerpass123'
        )

        url = reverse(
            'accept_request',
            args=[self.participation.id]
        )

        response = self.client.post(url)

        self.participation.refresh_from_db()

        self.assertEqual(self.participation.status, 'ACCEPTED')

        accepted_count = self.event.participation_requests.filter(
            status='ACCEPTED'
        ).count()

    
        self.assertLessEqual(
            accepted_count,
            self.event.max_participants
        )

    def test_owner_can_reject_request(self):
        self.client.login(
            username=self.owner.username,
            password='ownerpass123'
        )

        url = reverse(
            'reject_request', 
            args=[self.participation.id]
        )

        response = self.client.post(url)

        self.participation.refresh_from_db()

        self.assertEqual(
            self.participation.status,
            'REJECTED'
        )

    def test_request_after_the_event_status_is_full(self):
        User = get_user_model()

        second_participant = User.objects.create_user(
            username='participant2',
            email='participant2@test.com',
            password='testpass123'
        )

        participation = Participation.objects.create(
            user=second_participant,
            event=self.event,
            status='PENDING'
        )

        self.event.max_participants = 1
        self.event.save()

        self.participation.status = 'ACCEPTED'
        self.participation.save()

        self.event.status = 'FULL'
        self.event.save()

        self.client.login(
            username=self.owner.username, 
            password='ownerpass123'
        )

        url = reverse(
            'accept_request', 
            args=[participation.id]
        )

        response = self.client.post(url)

        participation.refresh_from_db()

        self.assertEqual(participation.status, 'PENDING')
        self.assertEqual(self.event.status, 'FULL')
        self.assertEqual(response.status_code, 302)

    def test_dublicate_request(self):
        participation = Participation(
            user=self.participant,
            event=self.event,
            status='PENDING'
        )

        self.participant.save()

        second_participation = Participation(
            user=self.participant,
            event=self.event,
            status='PENDING'
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                second_participation.save()


    def test_user_cannot_cancel_another_users_request(self):
        self.client.login(
            username=self.unauthorized.username, 
            password='unauthorizedpass123'
        )
               
        url = reverse(
            'cancel_request', 
            args=[self.participation.id]
        )
               
        response = self.client.post(url)
        
        self.participation.refresh_from_db()
        
        self.assertEqual(
            self.participation.status, 
            "PENDING"
        )   
        self.assertTrue(
            Participation.objects.filter(id=self.participation.id).exists()
        )

    def test_user_can_cancel_own_pending_request(self):
        self.client.login(
            username=self.participant.username,
            password='testpass123'
        )

        url = reverse(
            'cancel_request',
            args=[self.participation.id] 
        )

        response = self.client.post(url)

        self.assertFalse(
            Participation.objects.filter(id=self.participation.id).exists()        
        )
