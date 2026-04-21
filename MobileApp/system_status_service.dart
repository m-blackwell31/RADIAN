import 'dart:async';
import 'package:flutter/material.dart';

enum RadarStatus {
  active,
  offline,
}

class SystemStatusService extends ChangeNotifier {
  DateTime? _lastHeartbeatUtc;
  Timer? _watchdogTimer;

  DateTime? get lastHeartbeatUtc => _lastHeartbeatUtc;

  RadarStatus get radarStatus {
    if (_lastHeartbeatUtc == null) {
      return RadarStatus.offline;
    }

    final age = DateTime.now().toUtc().difference(_lastHeartbeatUtc!);

    if (age.inSeconds < 15) {
      return RadarStatus.active;
    } else {
      return RadarStatus.offline;
    }
  }

  void recordHeartbeat({DateTime? timestampUtc}) {
    _lastHeartbeatUtc = timestampUtc ?? DateTime.now().toUtc();
    notifyListeners();
  }

  void startWatchdog() {
    _watchdogTimer?.cancel();
    _watchdogTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      notifyListeners();
    });
  }

  void stopWatchdog() {
    _watchdogTimer?.cancel();
    _watchdogTimer = null;
  }

  String get statusLabel {
    switch (radarStatus) {
      case RadarStatus.active:
        return 'Active';
      case RadarStatus.offline:
        return 'Offline';
    }
  }

  String get lastHeartbeatLabel {
    if (_lastHeartbeatUtc == null) {
      return 'No heartbeat received';
    }

    final age = DateTime.now().toUtc().difference(_lastHeartbeatUtc!);

    if (age.inSeconds < 60) {
      return '${age.inSeconds}s ago';
    }

    final minutes = age.inMinutes;
    return '${minutes}m ago';
  }

  @override
  void dispose() {
    _watchdogTimer?.cancel();
    super.dispose();
  }
}
