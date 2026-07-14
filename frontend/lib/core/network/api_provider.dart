import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'api_client.dart';
import 'package:frontend/core/storage/secure_storage.dart';
import 'package:frontend/core/constants.dart';

final apiClientProvider = Provider<ApiClient>((ref) {
  final storage = ref.watch(secureStorageProvider);

  final client = ApiClient(storage: storage, baseUrl: AppConstants.baseUrl);

  ref.onDispose(() {
    client.close();
  });

  return client;
});
