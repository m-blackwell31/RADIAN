// ===========================================================
// File: /lib/data/fall_db.dart
// Purpose: Local Drift database for storing fall detection events.
// Requires: drift, drift_dev (dev), build_runner (dev),
//           sqlite3_flutter_libs, path_provider, path
// ===========================================================

import 'dart:io';
import 'package:drift/drift.dart';                 // Drift core (Table, Column, Database)
import 'package:drift/native.dart';                // NativeDatabase for Flutter mobile/desktop
import 'package:path/path.dart' as p;              // For joining paths safely
import 'package:path_provider/path_provider.dart'; // To find app documents dir

// This tells Drift to generate helper code next to this file.
// After saving, run: flutter pub run build_runner build --delete-conflicting-outputs
part 'fall_db.g.dart';

// -----------------------------------------------------------
// Table: FallEvents
// One row per detected fall (UTC timestamp, optional location/confidence).
// -----------------------------------------------------------
class FallEvents extends Table {
  // Auto-increment primary key
  IntColumn get id => integer().autoIncrement()();

  // Store times in UTC; convert to local for display
  DateTimeColumn get occurredAtUtc => dateTime()();

  // Optional room/location (e.g., "Living Room")
  TextColumn get location => text().nullable()();

  // Optional confidence (0.0 to 1.0)
  RealColumn get confidence => real().nullable()();

  // Where the entry came from (e.g., "gotify", "manual")
  TextColumn get source => text().withDefault(const Constant('gotify'))();

  // Optional: raw JSON payload for debugging/future analysis
  TextColumn get metaJson => text().nullable()();
}

// -----------------------------------------------------------
// Database: FallDb
// Main interface used by the app to insert and query events.
// -----------------------------------------------------------
@DriftDatabase(tables: [FallEvents])
class FallDb extends _$FallDb {
  FallDb() : super(_open()); // open/create the SQLite file

  // Increment this if you ever change the schema (add/remove columns, etc.)
  @override
  int get schemaVersion => 1;

  // Insert a new fall event
  Future<int> insertFall(FallEventsCompanion e) => into(fallEvents).insert(e);

  // Live stream of falls in [startUtc, endUtc)
  Stream<List<FallEvent>> watchFallsBetween(DateTime startUtc, DateTime endUtc) {
    return (select(fallEvents)
      ..where((t) =>
      t.occurredAtUtc.isBiggerOrEqualValue(startUtc) &
      t.occurredAtUtc.isSmallerThanValue(endUtc))
      ..orderBy([(t) => OrderingTerm.desc(t.occurredAtUtc)]))
        .watch();
  }
}

// -----------------------------------------------------------
// Database opener
// Creates/opens {appDocs}/radian_falls.sqlite using NativeDatabase.
// -----------------------------------------------------------
LazyDatabase _open() {
  return LazyDatabase(() async {
    // Pick a stable, app-private folder for the database file
    final dir = await getApplicationDocumentsDirectory();
    final file = File(p.join(dir.path, 'radian_falls.sqlite'));

    // You can also use NativeDatabase(file) if you don't want a background isolate.
    return NativeDatabase.createInBackground(file);
  });
}
