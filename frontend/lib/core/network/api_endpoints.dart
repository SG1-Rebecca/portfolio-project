import 'package:frontend/core/constants.dart';

class ApiEndpoints {
  static String get baseUrl => AppConstants.baseUrl;

  static const String login = '/auth/login/';
  static const String verifyOtp = '/auth/verify-otp/';
  static const String resendOtp = '/auth/resend-otp/';
  static const String toggle2FA = '/auth/toggle-2fa/';
  static const String logout = '/auth/logout/';
  static const String refreshToken = '/auth/token/refresh/';
  static const String register = '/auth/register/';

  static const String playerProfile = '/profiles/player/';
  static const String clubProfile = '/profiles/club/';

  static const String clubs = '/clubs/';

  static const String posts = '/posts/';
  static const String applications = '/applications/';
}
