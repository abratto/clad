import 'package:flutter/foundation.dart';

/// Manages login state for the Flutter UI. Calls POST /api/login on the
/// CLAD engine — same engine, same flow tokens as REST/GraphQL surfaces.
class AuthState extends ChangeNotifier {
  bool _isLoading = false;
  String? _sessionToken;
  String? _error;

  bool get isLoading => _isLoading;
  String? get sessionToken => _sessionToken;
  String? get error => _error;

  void setLoading(bool loading) {
    _isLoading = loading;
    _error = null;
    notifyListeners();
  }

  void loginSuccess(String token) {
    _isLoading = false;
    _sessionToken = token;
    _error = null;
    notifyListeners();
  }

  void loginError(String message) {
    _isLoading = false;
    _sessionToken = null;
    _error = message;
    notifyListeners();
  }
}
