import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:frontend/core/storage/secure_storage.dart';
import 'package:frontend/core/network/api_endpoints.dart';

class ApiClient {
  // Fields
  final http.Client _client;
  final SecureStorage _storage;
  final String _baseUrl;
  final Duration _connectTimeout;
  final Duration _receiveTimeout;

  // Constructor
  ApiClient({
    http.Client? client,
    required SecureStorage storage,
    String? baseUrl,
    Duration connectTimeout = const Duration(seconds: 30),
    Duration receiveTimeout = const Duration(seconds: 60),
  })  : _client = client ?? http.Client(),
        _storage = storage,
        _baseUrl = baseUrl ?? ApiEndpoints.baseUrl,
        _connectTimeout = connectTimeout,
        _receiveTimeout = receiveTimeout;

  // Public Methods

  Future<dynamic> get(String endpoint) async {
    final response = await _client.get(
      _buildUri(endpoint),
      headers: await _headers(),
    );
    return _handleResponse(response);
  }

  Future<dynamic> post(String endpoint, {Map<String, dynamic>? data}) async {
    final response = await _client.post(
      _buildUri(endpoint),
      headers: await _headers(),
      body: data != null ? jsonEncode(data) : null,
    );
    return _handleResponse(response);
  }

  Future<dynamic> put(String endpoint, {Map<String, dynamic>? data}) async {
    final response = await _client.put(
      _buildUri(endpoint),
      headers: await _headers(),
      body: data != null ? jsonEncode(data) : null,
    );
    return _handleResponse(response);
  }

  Future<dynamic> patch(String endpoint, {Map<String, dynamic>? data}) async {
    final response = await _client.patch(
      _buildUri(endpoint),
      headers: await _headers(),
      body: data != null ? jsonEncode(data) : null,
    );
    return _handleResponse(response);
  }

  Future<dynamic> delete(String endpoint) async {
    final response = await _client.delete(
      _buildUri(endpoint),
      headers: await _headers(),
    );
    return _handleResponse(response);
  }

  // Token Management

  Future<void> setToken(String token) async {
    await _storage.write('access_token', token);
  }

  Future<void> clearToken() async {
    await _storage.delete('access_token');
  }

  Future<String?> getToken() async {
    return await _storage.read('access_token');
  }

  // Private Methods

  Uri _buildUri(String endpoint) {
    final base = Uri.parse(_baseUrl);
    
    // Separate the path from the query parameters
    final uri = Uri.parse(endpoint);
    final path = uri.path;
    final query = uri.query;
    
    // Handle double slashes gracefully
    final fullPath = base.path.endsWith('/') && path.startsWith('/')
        ? base.path + path.substring(1)
        : base.path + path;
    
    return Uri(
      scheme: base.scheme,
      host: base.host,
      port: base.port,
      path: fullPath,
      query: query.isNotEmpty ? query : null,  // Add query parameters if present
    );
  }

  Future<Map<String, String>> _headers() async {
    final token = await _storage.read('access_token');
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  dynamic _handleResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return response.body.isEmpty ? null : jsonDecode(response.body);
    } else if (response.statusCode == 401) {
      throw Exception('Non autorisé - Token invalide ou expiré');
    } else {
      throw Exception('Erreur ${response.statusCode}: ${response.body}');
    }
  }

  // Cleanup

  void close() {
    _client.close();
  }
}