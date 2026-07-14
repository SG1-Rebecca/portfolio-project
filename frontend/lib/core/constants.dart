import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb;

class AppConstants {
  AppConstants._();

  static String get baseUrl {
    if (kIsWeb) {
      // Web → localhost
      return 'http://localhost:8000/api/v1/';
    } else if (Platform.isAndroid) {
      // Android emulator → 10.0.2.2
      return 'http://10.0.2.2:8000/api/v1/';
    } else if (Platform.isIOS) {
      // iOS simulator
      return 'http://localhost:8000/api/v1/';
    } else {
      // Others (Windows, macOS, Linux) → localhost
      return 'http://localhost:8000/api/v1/';
    }
  }

  // Temps de timeout
  static const Duration connectTimeout = Duration(seconds: 60);
  static const Duration receiveTimeout = Duration(seconds: 60);

  // Secure storage keys
  static const String accessTokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
  static const String userRoleKey = 'user_role';
  static const String userEmailKey = 'user_email';
}
