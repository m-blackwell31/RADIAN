// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'fall_db.dart';

// ignore_for_file: type=lint
class $FallEventsTable extends FallEvents
    with TableInfo<$FallEventsTable, FallEvent> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $FallEventsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
      'id', aliasedName, false,
      hasAutoIncrement: true,
      type: DriftSqlType.int,
      requiredDuringInsert: false,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('PRIMARY KEY AUTOINCREMENT'));
  static const VerificationMeta _occurredAtUtcMeta =
      const VerificationMeta('occurredAtUtc');
  @override
  late final GeneratedColumn<DateTime> occurredAtUtc =
      GeneratedColumn<DateTime>('occurred_at_utc', aliasedName, false,
          type: DriftSqlType.dateTime, requiredDuringInsert: true);
  static const VerificationMeta _locationMeta =
      const VerificationMeta('location');
  @override
  late final GeneratedColumn<String> location = GeneratedColumn<String>(
      'location', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _confidenceMeta =
      const VerificationMeta('confidence');
  @override
  late final GeneratedColumn<double> confidence = GeneratedColumn<double>(
      'confidence', aliasedName, true,
      type: DriftSqlType.double, requiredDuringInsert: false);
  static const VerificationMeta _sourceMeta = const VerificationMeta('source');
  @override
  late final GeneratedColumn<String> source = GeneratedColumn<String>(
      'source', aliasedName, false,
      type: DriftSqlType.string,
      requiredDuringInsert: false,
      defaultValue: const Constant('gotify'));
  static const VerificationMeta _metaJsonMeta =
      const VerificationMeta('metaJson');
  @override
  late final GeneratedColumn<String> metaJson = GeneratedColumn<String>(
      'meta_json', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  @override
  List<GeneratedColumn> get $columns =>
      [id, occurredAtUtc, location, confidence, source, metaJson];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'fall_events';
  @override
  VerificationContext validateIntegrity(Insertable<FallEvent> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('occurred_at_utc')) {
      context.handle(
          _occurredAtUtcMeta,
          occurredAtUtc.isAcceptableOrUnknown(
              data['occurred_at_utc']!, _occurredAtUtcMeta));
    } else if (isInserting) {
      context.missing(_occurredAtUtcMeta);
    }
    if (data.containsKey('location')) {
      context.handle(_locationMeta,
          location.isAcceptableOrUnknown(data['location']!, _locationMeta));
    }
    if (data.containsKey('confidence')) {
      context.handle(
          _confidenceMeta,
          confidence.isAcceptableOrUnknown(
              data['confidence']!, _confidenceMeta));
    }
    if (data.containsKey('source')) {
      context.handle(_sourceMeta,
          source.isAcceptableOrUnknown(data['source']!, _sourceMeta));
    }
    if (data.containsKey('meta_json')) {
      context.handle(_metaJsonMeta,
          metaJson.isAcceptableOrUnknown(data['meta_json']!, _metaJsonMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  FallEvent map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return FallEvent(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}id'])!,
      occurredAtUtc: attachedDatabase.typeMapping.read(
          DriftSqlType.dateTime, data['${effectivePrefix}occurred_at_utc'])!,
      location: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}location']),
      confidence: attachedDatabase.typeMapping
          .read(DriftSqlType.double, data['${effectivePrefix}confidence']),
      source: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}source'])!,
      metaJson: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}meta_json']),
    );
  }

  @override
  $FallEventsTable createAlias(String alias) {
    return $FallEventsTable(attachedDatabase, alias);
  }
}

class FallEvent extends DataClass implements Insertable<FallEvent> {
  final int id;
  final DateTime occurredAtUtc;
  final String? location;
  final double? confidence;
  final String source;
  final String? metaJson;
  const FallEvent(
      {required this.id,
      required this.occurredAtUtc,
      this.location,
      this.confidence,
      required this.source,
      this.metaJson});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['occurred_at_utc'] = Variable<DateTime>(occurredAtUtc);
    if (!nullToAbsent || location != null) {
      map['location'] = Variable<String>(location);
    }
    if (!nullToAbsent || confidence != null) {
      map['confidence'] = Variable<double>(confidence);
    }
    map['source'] = Variable<String>(source);
    if (!nullToAbsent || metaJson != null) {
      map['meta_json'] = Variable<String>(metaJson);
    }
    return map;
  }

  FallEventsCompanion toCompanion(bool nullToAbsent) {
    return FallEventsCompanion(
      id: Value(id),
      occurredAtUtc: Value(occurredAtUtc),
      location: location == null && nullToAbsent
          ? const Value.absent()
          : Value(location),
      confidence: confidence == null && nullToAbsent
          ? const Value.absent()
          : Value(confidence),
      source: Value(source),
      metaJson: metaJson == null && nullToAbsent
          ? const Value.absent()
          : Value(metaJson),
    );
  }

  factory FallEvent.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return FallEvent(
      id: serializer.fromJson<int>(json['id']),
      occurredAtUtc: serializer.fromJson<DateTime>(json['occurredAtUtc']),
      location: serializer.fromJson<String?>(json['location']),
      confidence: serializer.fromJson<double?>(json['confidence']),
      source: serializer.fromJson<String>(json['source']),
      metaJson: serializer.fromJson<String?>(json['metaJson']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'occurredAtUtc': serializer.toJson<DateTime>(occurredAtUtc),
      'location': serializer.toJson<String?>(location),
      'confidence': serializer.toJson<double?>(confidence),
      'source': serializer.toJson<String>(source),
      'metaJson': serializer.toJson<String?>(metaJson),
    };
  }

  FallEvent copyWith(
          {int? id,
          DateTime? occurredAtUtc,
          Value<String?> location = const Value.absent(),
          Value<double?> confidence = const Value.absent(),
          String? source,
          Value<String?> metaJson = const Value.absent()}) =>
      FallEvent(
        id: id ?? this.id,
        occurredAtUtc: occurredAtUtc ?? this.occurredAtUtc,
        location: location.present ? location.value : this.location,
        confidence: confidence.present ? confidence.value : this.confidence,
        source: source ?? this.source,
        metaJson: metaJson.present ? metaJson.value : this.metaJson,
      );
  FallEvent copyWithCompanion(FallEventsCompanion data) {
    return FallEvent(
      id: data.id.present ? data.id.value : this.id,
      occurredAtUtc: data.occurredAtUtc.present
          ? data.occurredAtUtc.value
          : this.occurredAtUtc,
      location: data.location.present ? data.location.value : this.location,
      confidence:
          data.confidence.present ? data.confidence.value : this.confidence,
      source: data.source.present ? data.source.value : this.source,
      metaJson: data.metaJson.present ? data.metaJson.value : this.metaJson,
    );
  }

  @override
  String toString() {
    return (StringBuffer('FallEvent(')
          ..write('id: $id, ')
          ..write('occurredAtUtc: $occurredAtUtc, ')
          ..write('location: $location, ')
          ..write('confidence: $confidence, ')
          ..write('source: $source, ')
          ..write('metaJson: $metaJson')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode =>
      Object.hash(id, occurredAtUtc, location, confidence, source, metaJson);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is FallEvent &&
          other.id == this.id &&
          other.occurredAtUtc == this.occurredAtUtc &&
          other.location == this.location &&
          other.confidence == this.confidence &&
          other.source == this.source &&
          other.metaJson == this.metaJson);
}

class FallEventsCompanion extends UpdateCompanion<FallEvent> {
  final Value<int> id;
  final Value<DateTime> occurredAtUtc;
  final Value<String?> location;
  final Value<double?> confidence;
  final Value<String> source;
  final Value<String?> metaJson;
  const FallEventsCompanion({
    this.id = const Value.absent(),
    this.occurredAtUtc = const Value.absent(),
    this.location = const Value.absent(),
    this.confidence = const Value.absent(),
    this.source = const Value.absent(),
    this.metaJson = const Value.absent(),
  });
  FallEventsCompanion.insert({
    this.id = const Value.absent(),
    required DateTime occurredAtUtc,
    this.location = const Value.absent(),
    this.confidence = const Value.absent(),
    this.source = const Value.absent(),
    this.metaJson = const Value.absent(),
  }) : occurredAtUtc = Value(occurredAtUtc);
  static Insertable<FallEvent> custom({
    Expression<int>? id,
    Expression<DateTime>? occurredAtUtc,
    Expression<String>? location,
    Expression<double>? confidence,
    Expression<String>? source,
    Expression<String>? metaJson,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (occurredAtUtc != null) 'occurred_at_utc': occurredAtUtc,
      if (location != null) 'location': location,
      if (confidence != null) 'confidence': confidence,
      if (source != null) 'source': source,
      if (metaJson != null) 'meta_json': metaJson,
    });
  }

  FallEventsCompanion copyWith(
      {Value<int>? id,
      Value<DateTime>? occurredAtUtc,
      Value<String?>? location,
      Value<double?>? confidence,
      Value<String>? source,
      Value<String?>? metaJson}) {
    return FallEventsCompanion(
      id: id ?? this.id,
      occurredAtUtc: occurredAtUtc ?? this.occurredAtUtc,
      location: location ?? this.location,
      confidence: confidence ?? this.confidence,
      source: source ?? this.source,
      metaJson: metaJson ?? this.metaJson,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (occurredAtUtc.present) {
      map['occurred_at_utc'] = Variable<DateTime>(occurredAtUtc.value);
    }
    if (location.present) {
      map['location'] = Variable<String>(location.value);
    }
    if (confidence.present) {
      map['confidence'] = Variable<double>(confidence.value);
    }
    if (source.present) {
      map['source'] = Variable<String>(source.value);
    }
    if (metaJson.present) {
      map['meta_json'] = Variable<String>(metaJson.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('FallEventsCompanion(')
          ..write('id: $id, ')
          ..write('occurredAtUtc: $occurredAtUtc, ')
          ..write('location: $location, ')
          ..write('confidence: $confidence, ')
          ..write('source: $source, ')
          ..write('metaJson: $metaJson')
          ..write(')'))
        .toString();
  }
}

abstract class _$FallDb extends GeneratedDatabase {
  _$FallDb(QueryExecutor e) : super(e);
  $FallDbManager get managers => $FallDbManager(this);
  late final $FallEventsTable fallEvents = $FallEventsTable(this);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities => [fallEvents];
}

typedef $$FallEventsTableCreateCompanionBuilder = FallEventsCompanion Function({
  Value<int> id,
  required DateTime occurredAtUtc,
  Value<String?> location,
  Value<double?> confidence,
  Value<String> source,
  Value<String?> metaJson,
});
typedef $$FallEventsTableUpdateCompanionBuilder = FallEventsCompanion Function({
  Value<int> id,
  Value<DateTime> occurredAtUtc,
  Value<String?> location,
  Value<double?> confidence,
  Value<String> source,
  Value<String?> metaJson,
});

class $$FallEventsTableTableManager extends RootTableManager<
    _$FallDb,
    $FallEventsTable,
    FallEvent,
    $$FallEventsTableFilterComposer,
    $$FallEventsTableOrderingComposer,
    $$FallEventsTableCreateCompanionBuilder,
    $$FallEventsTableUpdateCompanionBuilder> {
  $$FallEventsTableTableManager(_$FallDb db, $FallEventsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          filteringComposer:
              $$FallEventsTableFilterComposer(ComposerState(db, table)),
          orderingComposer:
              $$FallEventsTableOrderingComposer(ComposerState(db, table)),
          updateCompanionCallback: ({
            Value<int> id = const Value.absent(),
            Value<DateTime> occurredAtUtc = const Value.absent(),
            Value<String?> location = const Value.absent(),
            Value<double?> confidence = const Value.absent(),
            Value<String> source = const Value.absent(),
            Value<String?> metaJson = const Value.absent(),
          }) =>
              FallEventsCompanion(
            id: id,
            occurredAtUtc: occurredAtUtc,
            location: location,
            confidence: confidence,
            source: source,
            metaJson: metaJson,
          ),
          createCompanionCallback: ({
            Value<int> id = const Value.absent(),
            required DateTime occurredAtUtc,
            Value<String?> location = const Value.absent(),
            Value<double?> confidence = const Value.absent(),
            Value<String> source = const Value.absent(),
            Value<String?> metaJson = const Value.absent(),
          }) =>
              FallEventsCompanion.insert(
            id: id,
            occurredAtUtc: occurredAtUtc,
            location: location,
            confidence: confidence,
            source: source,
            metaJson: metaJson,
          ),
        ));
}

class $$FallEventsTableFilterComposer
    extends FilterComposer<_$FallDb, $FallEventsTable> {
  $$FallEventsTableFilterComposer(super.$state);
  ColumnFilters<int> get id => $state.composableBuilder(
      column: $state.table.id,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<DateTime> get occurredAtUtc => $state.composableBuilder(
      column: $state.table.occurredAtUtc,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get location => $state.composableBuilder(
      column: $state.table.location,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<double> get confidence => $state.composableBuilder(
      column: $state.table.confidence,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get source => $state.composableBuilder(
      column: $state.table.source,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));

  ColumnFilters<String> get metaJson => $state.composableBuilder(
      column: $state.table.metaJson,
      builder: (column, joinBuilders) =>
          ColumnFilters(column, joinBuilders: joinBuilders));
}

class $$FallEventsTableOrderingComposer
    extends OrderingComposer<_$FallDb, $FallEventsTable> {
  $$FallEventsTableOrderingComposer(super.$state);
  ColumnOrderings<int> get id => $state.composableBuilder(
      column: $state.table.id,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<DateTime> get occurredAtUtc => $state.composableBuilder(
      column: $state.table.occurredAtUtc,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get location => $state.composableBuilder(
      column: $state.table.location,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<double> get confidence => $state.composableBuilder(
      column: $state.table.confidence,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get source => $state.composableBuilder(
      column: $state.table.source,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));

  ColumnOrderings<String> get metaJson => $state.composableBuilder(
      column: $state.table.metaJson,
      builder: (column, joinBuilders) =>
          ColumnOrderings(column, joinBuilders: joinBuilders));
}

class $FallDbManager {
  final _$FallDb _db;
  $FallDbManager(this._db);
  $$FallEventsTableTableManager get fallEvents =>
      $$FallEventsTableTableManager(_db, _db.fallEvents);
}
