// ===============================================================
// gotify_service.dart
// ---------------------------------------------------------------
// This file defines a simple class (GotifyService) that lets your
// Flutter app communicate with a Gotify server for:
//   1) Sending alert messages (via HTTP POST)
//   2) Receiving live notifications (via WebSocket)
//
// The class is lightweight and stateless: you can call `send()`
// to push messages, and `connect()` to listen for incoming ones.
// ===============================================================

import 'dart:convert'; // For JSON encoding/decoding
import 'package:http/http.dart' as http; // For HTTP requests (sending messages)
import 'package:web_socket_channel/web_socket_channel.dart'; // For live message streaming
import 'package:flutter/foundation.dart' show debugPrint;

// ---------------------------------------------------------------
// Typedef: describes the callback function signature
// ---------------------------------------------------------------
// When Gotify pushes a message over WebSocket, your app's callback
// receives the decoded JSON map. You’ll pass this function in
// when calling connect() from your main.dart.
typedef GotifyCallback = Future<void> Function(Map<String, dynamic> msg);
typedef GotifyStatusCallback = void Function(bool connected);

// ---------------------------------------------------------------
// CLASS: GotifyService
// ---------------------------------------------------------------
// Handles all communication between the RADIAN app and a Gotify server.
// Example usage from main.dart:
//
//   final gotify = GotifyService(
//     baseUrl: 'https://192.168.1.50:8080',
//     clientToken: 'YOUR_CLIENT_TOKEN',
//   );
//   gotify.connect((msg) { print(msg); });
//
//   gotify.send('Test Title', 'Hello from RADIAN');
//
// ---------------------------------------------------------------
class GotifyService {
  // -------------------------------------------------------------
  // Instance variables
  // -------------------------------------------------------------
  final String baseUrl;   // e.g., https://192.168.1.50:8080
  final String clientToken;  // App token generated from Gotify dashboard

  WebSocketChannel? _channel; // Active WebSocket connection (if connected)

  // -------------------------------------------------------------
  // Constructor
  // -------------------------------------------------------------
  GotifyService({required this.baseUrl, required this.clientToken});

  // -------------------------------------------------------------
  // METHOD: send()
  // -------------------------------------------------------------
  // Sends a message to Gotify using its REST API endpoint `/message`.
  // You can use this for debugging or when your app wants to broadcast
  // an event to all Gotify clients.
  //
  // Example:
  // await send('ALERT', 'Fall detected in bedroom', priority: 10);
  // -------------------------------------------------------------
  Future<void> send(String title, String message, {int priority = 5}) async {
    // Build the target URI, appending "/message"
    final uri = Uri.parse('$baseUrl/message');

    // Perform an HTTP POST with the required Gotify headers
    final resp = await http.post(
      uri,
      headers: {
        'Content-Type': 'application/json',
        'X-Gotify-Key': clientToken, // Token authenticates this client
      },
      // The Gotify server expects JSON like:
      // {"title": "ALERT", "message": "details...", "priority": 5}
      body: jsonEncode({
        'title': title,
        'message': message,
        'priority': priority,
      }),
    );

    // Throw an exception if Gotify responded with an error
    if (resp.statusCode >= 300) {
      throw Exception('Gotify send failed: ${resp.statusCode} ${resp.body}');
    }
  }

  // -------------------------------------------------------------
  // METHOD: connect()
  // -------------------------------------------------------------
  // Opens a persistent WebSocket connection to Gotify’s `/stream`
  // endpoint, so your app can receive push notifications instantly.
  //
  // You must provide a callback function (GotifyCallback) that runs
  // whenever a new message arrives from the server.
  //
  // Example:
  //   gotify.connect((msg) {
  //     print('Received: ${msg['title']} -> ${msg['message']}');
  //   });
  //
  // -------------------------------------------------------------
  void connect(GotifyCallback onMessage, {GotifyStatusCallback? onStatus}) {
    // Gotify supports both http/ws and https/wss schemes.
    final isHttps = baseUrl.toLowerCase().startsWith('https');
    final scheme = isHttps ? 'wss' : 'ws'; // Use secure socket for https URLs

    // Remove "http://" or "https://" and trailing slash from baseUrl
    final host = baseUrl
        .replaceFirst(RegExp(r'^https?://'), '') // strip scheme
        .replaceFirst(RegExp(r'/$'), '');         // strip trailing slash

    // Build the final WebSocket URL
    // Example: wss://your-server/stream?token=YOUR_APP_TOKEN
    final wsUrl = Uri.parse('$scheme://$host/stream?token=$clientToken');

    // Close any existing connection first to avoid duplicates
    _channel?.sink.close();

    // Open a new WebSocket connection
    _channel = WebSocketChannel.connect(wsUrl);
    onStatus?.call(true);

    // Listen for incoming messages from Gotify
    _channel!.stream.listen(
          (event) {
        // Gotify sends each message as a JSON string
        try {
          final data = jsonDecode(event);
          // If the message is a valid JSON map, pass it to your callback
          if (data is Map<String, dynamic>) {
            onMessage(data).catchError((e, st) {
              debugPrint('Gotify onMessage error: $e');
              debugPrint(st);
            });
          }
        } catch (_) {
          // Ignore malformed messages silently
        }
      },
      // Handle WebSocket errors (e.g., network issues)
      onError: (error) {
        debugPrint('Gotify WebSocket error: $error');
        onStatus?.call(false);
      },
      // Handle normal or unexpected connection closures
      onDone: () {
        debugPrint('Gotify WebSocket connection closed');
        onStatus?.call(false);
      },
    );
  }

  // -------------------------------------------------------------
  // METHOD: disconnect()
  // -------------------------------------------------------------
  // Closes the WebSocket connection gracefully.
  // You should call this in your main app’s dispose() method
  // to prevent memory leaks.
  // -------------------------------------------------------------
  void disconnect() {
    _channel?.sink.close(); // Close WebSocket if open
    _channel = null;        // Release reference
  }
}
