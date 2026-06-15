from django.db import models
from django.core.exceptions import ValidationError

from core.enums import Status, SkillLevel, ApplicationStatus, Position, SectionCategory, Gender

from core.models import BaseModel
from accounts.models import PlayerProfile, ClubProfile


# Create your models here.
class RecruitmentPost(BaseModel):
    """
    Recruitment offer published by the club
    """
    club = models.ForeignKey(ClubProfile, on_delete=models.CASCADE, related_name='recruitment_post')
    category = models.CharField(max_length=50, choices=SectionCategory)
    position_needed = models.CharField(max_length=50, choices=Position)
    status = models.CharField(max_length=50, choices=Status)
    title = models.CharField(blank=False, null=False, max_length=150)
    level_required = models.CharField(max_length=50, choices=SkillLevel)
    region = models.CharField(blank=False, null=False, max_length=50)
    description = models.TextField(blank=True, null=True)
    application_deadline = models.DateField()

    def __str__(self):
        return f" {self.club} - {self.title}"

    class Meta:
        ordering = ('-application_deadline',)
        verbose_name = 'Recruitment Post'
        verbose_name_plural = 'Recruitment Posts'


class Application(BaseModel):
    """
    Application submitted by a player to a recruitment post
    """
    player = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name='player_applications')
    post = models.ForeignKey(RecruitmentPost, on_delete=models.CASCADE, related_name='applications')
    player_message = models.TextField(blank=True)
    contact_revealed = models.BooleanField(default=False)
    status = models.CharField(max_length=50, choices=ApplicationStatus, default=ApplicationStatus.PENDING)

    def clean(self):
        super().clean()

        if not self.post_id or not self.player_id:
            return

        if self.post.category == SectionCategory.MEN and self.player.gender != Gender.MALE:
            raise ValidationError("This position is reserved for men's teams.")

        if self.post.category == SectionCategory.WOMEN and self.player.gender != Gender.FEMALE:
            raise ValidationError("This position is reserved for women's teams.")

    def __str__(self):
        player_name = self.player.user.get_full_name().strip() or 'Unknown'
        club_name = self.post.club.club_name
        return (
            f'[{self.status}] {player_name} -> {self.post.title} '
            f'{club_name} '
            f'{self.post.position_needed} • {self.post.level_required}'
        )

    class Meta:
        unique_together = ('player', 'post')
        ordering = ['-created_at']
