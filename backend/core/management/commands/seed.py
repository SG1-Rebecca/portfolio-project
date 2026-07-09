"""
Management command: generates demo data.

- 50 players (25 male / 25 female), all adults
- 10 futsal clubs distributed across France

Installation:
    pip install Faker

Usage:
    python manage.py seed
    python manage.py seed --flush
    python manage.py seed --with-posts
"""

import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from faker import Faker

from accounts.models import User, PlayerProfile, ClubProfile
from recruitment.models import RecruitmentPost, Application
from core.enums import (
    Gender, SkillLevel, PlayerPosition, RecruitmentPosition, Role,
    Status, SectionCategory,
)

fake = Faker('fr_FR')

# Villes françaises avec coordonnées approximatives de région, pour répartir les clubs
FRENCH_CITIES = [
    {"city": "Paris", "region": "Île-de-France", "district": "Paris"},
    {"city": "Marseille", "region": "Provence-Alpes-Côte d'Azur", "district": "Bouches-du-Rhône"},
    {"city": "Lyon", "region": "Auvergne-Rhône-Alpes", "district": "Rhône"},
    {"city": "Toulouse", "region": "Occitanie", "district": "Haute-Garonne"},
    {"city": "Nice", "region": "Provence-Alpes-Côte d'Azur", "district": "Alpes-Maritimes"},
    {"city": "Nantes", "region": "Pays de la Loire", "district": "Loire-Atlantique"},
    {"city": "Strasbourg", "region": "Grand Est", "district": "Bas-Rhin"},
    {"city": "Montpellier", "region": "Occitanie", "district": "Hérault"},
    {"city": "Bordeaux", "region": "Nouvelle-Aquitaine", "district": "Gironde"},
    {"city": "Lille", "region": "Hauts-de-France", "district": "Nord"},
]

FUTSAL_CLUB_SUFFIXES = ["Futsal Club", "FC Futsal", "Futsal Academy", "Futsal Élite", "Futsal"]


def random_adult_birthdate(min_age=18, max_age=40):
    today = date.today()
    age = random.randint(min_age, max_age)
    # marge de jours aléatoire pour éviter que tout le monde ait exactement le même jour
    delta_days = random.randint(0, 364)
    return today.replace(year=today.year - age) - timedelta(days=delta_days)


def random_foundation_date():
    start = date(1970, 1, 1)
    end = date(2015, 1, 1)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


class Command(BaseCommand):
    help = "Génère 50 joueurs (25H/25F majeurs) et 10 clubs de futsal répartis en France."

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help="Supprime les données générées précédemment (par email se terminant en @demo.local) avant de regénérer.",
        )
        parser.add_argument(
            '--with-posts',
            action='store_true',
            help="Génère aussi des annonces de recrutement et quelques candidatures.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['flush']:
            self.stdout.write("Suppression des anciennes données de démo...")
            deleted, _ = User.objects.filter(email__endswith='@demo.com').delete()
            self.stdout.write(self.style.WARNING(f"{deleted} enregistrements supprimés."))

        clubs = self.create_clubs()
        players = self.create_players()

        if options['with_posts']:
            self.create_posts_and_applications(clubs, players)

        self.stdout.write(self.style.SUCCESS(
            f"Terminé : {len(clubs)} clubs, {len(players)} joueurs créés."
        ))

    def create_clubs(self):
        self.stdout.write("Création des 10 clubs de futsal...")
        clubs = []
        for i, location in enumerate(FRENCH_CITIES):
            email = f"club{i+1}@demo.com"
            user = User.objects.create_user(
                email=email,
                password="Demo1234!",
                birth_date=random_adult_birthdate(25, 60),
                role=Role.CLUB,
                is_active=True,
            )
            club_name = f"{location['city']} {random.choice(FUTSAL_CLUB_SUFFIXES)}"
            club = ClubProfile.objects.create(
                user=user,
                club_name=club_name,
                president_name=fake.name(),
                foundation_date=random_foundation_date(),
                city=location['city'],
                country="France",
                league=f"Ligue {location['region']}",
                district=location['district'],
                social_link=f"https://instagram.com/{club_name.lower().replace(' ', '')}",
                is_verified=random.choice([True, True, False]),  # majorité vérifiés
            )
            clubs.append(club)
        return clubs

    def create_players(self):
        self.stdout.write("Creating 50 players (25 men / 25 women)...")
        players = []
        positions = list(PlayerPosition.values)
        levels = list(SkillLevel.values)

        for gender, count in [(Gender.MALE, 25), (Gender.FEMALE, 25)]:
            for i in range(count):
                first_name = fake.first_name_male() if gender == Gender.MALE else fake.first_name_female()
                last_name = fake.last_name()
                email = f"{first_name.lower()}.{last_name.lower()}{i}@demo.com".replace(' ', '')

                user = User.objects.create_user(
                    email=email,
                    password="Demo1234!",
                    birth_date=random_adult_birthdate(18, 35),
                    role=Role.PLAYER,
                    is_active=True,
                )
                player = PlayerProfile.objects.create(
                    user=user,
                    first_name=first_name,
                    last_name=last_name,
                    gender=gender,
                    position=random.choice(positions),
                    level=random.choice(levels),
                    biography=fake.text(max_nb_chars=150),
                    is_verified=random.choice([True, False]),
                )
                players.append(player)
        return players

    def create_posts_and_applications(self, clubs, players):
        self.stdout.write("Creating recruitment posts and applications...")
        positions = list(RecruitmentPosition.values)
        levels = list(SkillLevel.values)
        categories = list(SectionCategory.values)

        posts = []
        for club in clubs:
            for _ in range(random.randint(1, 3)):
                category = random.choice(categories)
                post = RecruitmentPost.objects.create(
                    club=club,
                    title=f"Recrutement {dict(RecruitmentPosition.choices)[random.choice(positions)]} - {club.city}",
                    status=Status.OPEN,
                    category=category,
                    position_needed=random.choice(positions),
                    level_required=random.choice(levels),
                    region=club.district,
                    description=fake.paragraph(nb_sentences=5),
                    application_deadline=date.today() + timedelta(days=random.randint(10, 60)),
                )
                posts.append(post)

        # candidatures aléatoires cohérentes avec genre/position si possible, sinon on ignore les erreurs de clean()
        for player in players:
            eligible_posts = [
                p for p in posts
                if (p.category == SectionCategory.MEN and player.gender == Gender.MALE)
                or (p.category == SectionCategory.WOMEN and player.gender == Gender.FEMALE)
            ]
            if not eligible_posts or random.random() > 0.4:
                continue
            post = random.choice(eligible_posts)
            try:
                Application.objects.create(
                    post=post,
                    player=player,
                    player_message=fake.sentence(nb_words=12),
                )
            except Exception:
                # Skip invalid application due to validation constraints
                continue