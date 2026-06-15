import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from datetime import date

from core.models import BaseModel
from core.enums import Gender, SkillLevel, Role


# Create your models here.
class User(AbstractUser):
    """

    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    is_2fa_enabled = models.BooleanField(default=False)
    birth_date = models.DateField(null=True, blank=True)
    role = models.CharField(null=True, blank=True, choices=Role, max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

    def is_adult(self):
        """
        Check if the user is an adult (18 years or older)
        based on their birth date.
        """
        if not self.birth_date:
            return False

        today = date.today()
        age = today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return age >= 18

    def get_profile(self):
        if hasattr(self, 'playerprofile'):
            return self.playerprofile
        if hasattr(self, 'clubprofile'):
            return self.clubprofile


class PlayerProfile(BaseModel):
    """

    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=50, choices=Gender)
    level = models.CharField(max_length=50, choices=SkillLevel)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.get_full_name()}'


class ClubProfile(BaseModel):
    """

    """
    club_name = models.CharField(blank=False, null=False, max_length=50)
    president_name = models.CharField(blank=False, null=False, max_length=128)
    foundation_date = models.DateField()
    city = models.CharField(blank=False, null=False, max_length=50)
    country = models.CharField(blank=False, null=False, max_length=50)
    league = models.CharField(blank=False, null=False, max_length=50)
    district = models.CharField(blank=False, null=False, max_length=50)
    social_link = models.URLField(max_length=200)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.club_name} | ({self.city}, {self.country}) | {self.league}'
