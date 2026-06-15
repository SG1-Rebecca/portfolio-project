from django.test import TestCase

# Create your tests here.
class TestEnums(TestCase):
    def test_skill_level_enum(self):
        from backend.core.enums import SkillLevel
        self.assertEqual(SkillLevel.BEGINNER.value, 'BEGINNER')
        self.assertEqual(SkillLevel.INTERMEDIATE.value, 'INTERMEDIATE')
        self.assertEqual(SkillLevel.ADVANCED.value, 'ADVANCED')
        self.assertEqual(SkillLevel.PRO.value, 'PRO')

