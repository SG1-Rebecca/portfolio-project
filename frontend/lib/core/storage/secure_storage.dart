// lib/core/storage/secure_storage.dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final secureStorageProvider = Provider<SecureStorage>((ref) {
  return SecureStorage();
});

class SecureStorage {
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  // Generic Storage Methods
  Future<void> write(String key, String value) async {
    await _storage.write(key: key, value: value);
  }

  Future<String?> read(String key) async {
    return await _storage.read(key: key);
  }

  Future<void> delete(String key) async {
    await _storage.delete(key: key);
  }

  Future<void> clear() async {
    await _storage.deleteAll();
  }

  // Auth-Specific Methods
  Future<void> saveTokens({
    required String access,
    required String refresh,
  }) async {
    await write('access_token', access);
    await write('refresh_token', refresh);
  }

  Future<String?> getAccessToken() async {
    return await read('access_token');
  }

  Future<String?> getRefreshToken() async {
    return await read('refresh_token');
  }

  Future<void> saveUserRole(String role) async {
    await write('user_role', role);
  }

  Future<String?> getUserRole() async {
    return await read('user_role');
  }

  Future<void> saveUserEmail(String email) async {
    await write('user_email', email);
  }

  Future<String?> getUserEmail() async {
    return await read('user_email');
  }
}
