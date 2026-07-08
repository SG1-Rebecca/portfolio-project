import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models

from datetime import date

from core.models import BaseModel
from core.enums import Gender, SkillLevel, Role, PlayerPosition
from .managers import UserManager


# Create your models here.
class User(AbstractBaseUser, PermissionsMixin):
    """
    
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_2fa_enabled = models.BooleanField(default=False)
    birth_date = models.DateField()
    role = models.CharField(null=True, blank=True, choices=Role, max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['birth_date']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

    def clean(self):
        super().clean()
        if self.birth_date and not self.is_adult():
            raise ValidationError({
                'birth_date': f"Minimum age requirement: 18 years old."
            })

    def is_adult(self):
        if not self.birth_date:
            return False
        today = date.today()
        age = (today.year - self.birth_date.year
               - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day)))
        return age >= 18

    def get_profile(self):
        if hasattr(self, 'playerprofile'):
            return self.playerprofile
        if hasattr(self, 'clubprofile'):
            return self.clubprofile
        return None


class PlayerProfile(BaseModel):
    """

    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='playerprofile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=50, choices=Gender)
    position = models.CharField(max_length=50, choices=PlayerPosition)
    level = models.CharField(max_length=50, choices=SkillLevel)
    biography = models.TextField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class ClubProfile(BaseModel):
    """

    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='clubprofile')
    club_name = models.CharField(max_length=50)
    president_name = models.CharField(max_length=128)
    foundation_date = models.DateField()
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    league = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    social_link = models.URLField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.club_name} | ({self.city}, {self.country}) | {self.league}'
