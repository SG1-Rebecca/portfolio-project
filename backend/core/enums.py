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


class PlayerPosition(models.TextChoices):
    """
    Real-field positions for a Player's profile.
    """
    GOALKEEPER = 'GOALKEEPER', 'Goalkeeper'
    DEFENDER = 'DEFENDER', 'Defender'
    MIDFIELDER = 'MIDFIELDER', 'Midfielder'
    FORWARD = 'FORWARD', 'Forward'
    UNIVERSAL = 'UNIVERSAL', 'Universal (Versatile)'


class RecruitmentPosition(models.TextChoices):
    """
    Positions a Club can target in a recruitment post.
    """
    GOALKEEPER = 'GOALKEEPER', 'Goalkeeper'
    DEFENDER = 'DEFENDER', 'Defender'
    MIDFIELDER = 'MIDFIELDER', 'Midfielder'
    FORWARD = 'FORWARD', 'Forward'
    ANY = 'ANY', 'Any Position Open'


class SectionCategory(models.TextChoices):
    """
    Category for recruitment sections
    """
    MEN = 'MEN', 'Men'
    WOMEN = 'WOMEN', 'Women'
