import '../../core/network/api_client.dart';

class ConversationRepository {
  final _dio = ApiClient.instance.dio;
  Future<List<Map<String, dynamic>>> list() async {
    final response = await _dio.get('/conversations');
    return (response.data as List).map((item) => Map<String, dynamic>.from(item as Map)).toList();
  }
}
