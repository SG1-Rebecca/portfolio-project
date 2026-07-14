enum UserRole { player, club }

enum Gender { male, female }

enum SkillLevel { beginner, intermediate, advanced, pro }

enum PlayerPosition { goalkeeper, defender, midfielder, forward, universal }

enum RecruitmentPosition { goalkeeper, defender, midfielder, forward, any }

enum RecruitmentStatus { open, closed }

enum SectionCategory { men, women }

enum ApplicationStatus { pending, accepted, rejected, withdrawn }

extension UserRoleX on UserRole {
  String get value => name.toUpperCase();
  static UserRole fromString(String s) =>
      UserRole.values.firstWhere((e) => e.value == s.toUpperCase());
}

extension ApplicationStatusX on ApplicationStatus {
  String get value => name.toUpperCase();

  static ApplicationStatus fromString(String s) =>
      ApplicationStatus.values.firstWhere((e) => e.value == s.toUpperCase());

  String get label => switch (this) {
    ApplicationStatus.pending => 'Pending',
    ApplicationStatus.accepted => 'Accepted',
    ApplicationStatus.rejected => 'Rejected',
    ApplicationStatus.withdrawn => 'Withdrawn',
  };
}

extension RecruitmentStatusX on RecruitmentStatus {
  String get value => name.toUpperCase();
  static RecruitmentStatus fromString(String s) =>
      RecruitmentStatus.values.firstWhere((e) => e.value == s.toUpperCase());
}
