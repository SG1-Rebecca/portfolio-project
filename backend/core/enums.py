from django.db import models


class SkillLevel(models.TextChoices):
    """
    Skill Levels of the player
    """
    BEGINNER = 'BEGINNER', 'Beginner'
    INTERMEDIATE = 'INTERMEDIATE', 'Intermediate'
    ADVANCED = 'ADVANCED', 'Advanced'
    PRO = 'PRO', 'Pro'


class Gender(models.TextChoices):
    """
    Genders of the player
    """
    MALE = 'MALE', 'Male'
    FEMALE = 'FEMALE', 'Female'


class Role(models.TextChoices):
    """
    User roles
    """
    PLAYER = 'PLAYER', 'Player'
    CLUB = 'CLUB', 'Club'


class Status(models.TextChoices):
    """
    Recruitment post status
    """
    OPEN = 'OPEN', 'Open'
    CLOSED = 'CLOSED', 'Closed'


class ApplicationStatus(models.TextChoices):
    """"
    Application status
    """
    PENDING = 'PENDING', 'Pending'
    ACCEPTED = 'ACCEPTED', 'Accepted'
    REJECTED = 'REJECTED', 'Rejected'
    WITHDRAWN = 'WITHDRAWN', 'Withdrawn'
