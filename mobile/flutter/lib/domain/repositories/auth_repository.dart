import '../../core/network/api_client.dart';
import '../../core/platform/koras_platform_bridge.dart';

class AuthRepository {
  final _dio = ApiClient.instance.dio;

  Future<void> register({required String phone, required String name, required String password}) async {
    final device = await KorasPlatformBridge.getDeviceInfo();
    final response = await _dio.post('/auth/register', data: {
      'phone': phone,
      'display_name': name,
      'password': password,
      'device_identifier': device['device_identifier'] ?? 'unknown',
      'android_version': device['android_version'] ?? '',
    });
    await ApiClient.instance.saveToken(response.data['access_token'] as String);
  }

  Future<void> login({required String phone, required String password}) async {
    final device = await KorasPlatformBridge.getDeviceInfo();
    final response = await _dio.post('/auth/login', data: {
      'phone': phone,
      'password': password,
      'device_identifier': device['device_identifier'] ?? 'unknown',
    });
    await ApiClient.instance.saveToken(response.data['access_token'] as String);
  }
}
