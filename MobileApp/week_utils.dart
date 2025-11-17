// ===========================================================
// File: /lib/features/fall_log/week_utils.dart
// Purpose: Helper functions for determining start/end of weeks
// and generating user-friendly week labels.
// ===========================================================

import 'package:intl/intl.dart';

// -----------------------------------------------------------
// startOfWeekLocal()
// Returns the start (Sunday 00:00) of the week for a given local date.
// -----------------------------------------------------------
DateTime startOfWeekLocal(DateTime local) {
  final dow = local.weekday % 7; // Sunday = 0
  final start = DateTime(local.year, local.month, local.day)
      .subtract(Duration(days: dow));
  return DateTime(start.year, start.month, start.day);
}

// -----------------------------------------------------------
// endOfWeekLocal()
// Returns the end of the week (exclusive bound: next Sunday 00:00).
// -----------------------------------------------------------
DateTime endOfWeekLocal(DateTime local) =>
    startOfWeekLocal(local).add(const Duration(days: 7));

// -----------------------------------------------------------
// weekLabel()
// Returns a readable string like "Oct 27–Nov 2, 2025".
// -----------------------------------------------------------
String weekLabel(DateTime weekStartLocal) {
  final f = DateFormat('MMM d');
  final fYear = DateFormat('y');
  final end = weekStartLocal.add(const Duration(days: 6));

  // Check if start and end fall in the same year
  final sameYear = fYear.format(weekStartLocal) == fYear.format(end);

  return sameYear
      ? '${f.format(weekStartLocal)}–${f.format(end)}, ${fYear.format(end)}'
      : '${f.format(weekStartLocal)}, ${fYear.format(weekStartLocal)} – '
      '${f.format(end)}, ${fYear.format(end)}';
}
