// ==========================================================
// RADIAN - UI + Gotify Integration (Fully Commented)
// ----------------------------------------------------------
// This app demonstrates the RADIAN project's core workflow:
// • Alerts tab: "Simulate Fall" adds a CRITICAL alert.
// • Every 30s, a "Reminder" is added until acknowledged.
// • Home tab shows a red "Attention required" banner while active.
// • Settings tab allows connection to a Gotify server for live alerts.
// ==========================================================

import 'dart:async';                     // For periodic timers
import 'package:flutter/material.dart';  // Flutter UI framework
import 'gotify_service.dart';            // Custom file to handle Gotify comms

// >>> ADDED: imports for the caregiver Fall Log feature & local DB
import 'package:radian/data/fall_db.dart';
import 'package:radian/features/fall_log/fall_log_tab.dart';
import 'package:shared_preferences/shared_preferences.dart'; //for saving theme

void main() => runApp(const RadianApp()); // Entry point for Flutter

// ----------------------------------------------------------
// ROOT APP (MaterialApp wrapper)
// ----------------------------------------------------------


class RadianApp extends StatefulWidget {
  const RadianApp({super.key});

  @override
  State<RadianApp> createState() => _RadianAppState();
}

class _RadianAppState extends State<RadianApp> {
  // --------------------------------------------------------
  // THEME STATE
  // --------------------------------------------------------
  ThemeMode _themeMode = ThemeMode.system; // default to system theme

  // Load saved theme preference from Shared Preferences
  @override
  void initState() {
    super.initState();
    _loadTheme(); // call async loader below
  }

  Future<void> _loadTheme() async {
    final prefs = await SharedPreferences.getInstance();
    final savedIndex = prefs.getInt('themeMode') ?? 0; // 0=system, 1=light, 2=dark
    setState(() {
      _themeMode = ThemeMode.values[savedIndex];
    });
  }

  // Save theme choice and apply immediately
  Future<void> _setTheme(ThemeMode mode) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt('themeMode', mode.index);
    setState(() {
      _themeMode = mode;
    });
  }

  // ---------------------------------------------------
  // APP BUILD
  // ---------------------------------------------------
  @override
  Widget build(BuildContext context) {
    const seed = Color(0xFF1069FF); // RADIAN brand blue color

    return MaterialApp(
      title: 'RADIAN',
      debugShowCheckedModeBanner: false, // Hide "Debug" banner
      themeMode: _themeMode,
      // ----- LIGHT THEME -----
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: seed,
          brightness: Brightness.light,
        ),
      ),
      // ----- DARK THEME -----
      darkTheme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: seed,
          brightness: Brightness.dark,
        ),
      ),

      home: const _Root()
    );
  }
}

// ----------------------------------------------------------
// MAIN STATEFUL SHELL (_Root)
// ----------------------------------------------------------
// Handles navigation (bottom tabs), reminders, alerts, and Gotify state.
class _Root extends StatefulWidget {
  const _Root({super.key});
  @override
  State<_Root> createState() => _RootState();
}

class _RootState extends State<_Root> with WidgetsBindingObserver {
  // -------------------------------
  // UI NAVIGATION & ALERT STATE
  // -------------------------------
  int _index = 0;                 // Which bottom-nav tab is selected
  final List<_Alert> _alerts = []; // Stores all alerts shown in the app

  // -------------------------------
  // REMINDER SYSTEM VARIABLES
  // -------------------------------
  bool _needsAttention = false; // True while reminders are active
  Timer? _reminderTimer;        // The periodic reminder timer
  final Duration reminderInterval = const Duration(seconds: 30);
  _Alert? get _last => _alerts.isEmpty ? null : _alerts.last;

  // -------------------------------
  // GOTIFY CONNECTION VARIABLES
  // -------------------------------
  String _serverUrl = '';         // User-entered Gotify server URL
  String _appToken = '';          // User-entered Gotify app token
  GotifyService? _gotify;         // Active Gotify connection instance

  // >>> ADDED: shared DB instance for the Fall Log tab (and optional ingestion)
  // Keeping it local to _Root so we don't touch your app structure.
  final FallDb _fallDb = FallDb();

  // -------------------------------
  // LIFECYCLE MANAGEMENT
  // -------------------------------
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this); // Watch app lifecycle events
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _reminderTimer?.cancel(); // Stop any running reminder timer
    _gotify?.disconnect();    // Close Gotify WebSocket connection

    // >>> ADDED: close DB (optional; safe to omit on mobile, but clean)
    _fallDb.close();

    super.dispose();
  }

  // Called when app returns to the foreground.
  // Used to automatically stop reminders when the caregiver reopens the app.
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) _acknowledgeAttention();
    super.didChangeAppLifecycleState(state);
  }

  // ----------------------------------------------------------
  // LOCAL ALERT SIMULATION (for demo)
  // ----------------------------------------------------------
  // Adds a "FALL DETECTED" alert manually when the button is pressed.
  void _addInitialFallAlert() {
    _alerts.add(
      _Alert(
        DateTime.now(),
        'FALL DETECTED',
        'Possible fall event. Verify occupant safety.',
        isReminder: false,
      ),
    );
    _startReminders(); // Begin periodic follow-up reminders
    setState(() {});   // Refresh the UI
  }

  // ----------------------------------------------------------
  // REMINDER HANDLING
  // ----------------------------------------------------------
  // Starts a repeating timer that adds a "Reminder" alert every 30 seconds.
  void _startReminders() {
    _needsAttention = true;
    _reminderTimer?.cancel(); // Prevent overlapping timers
    _reminderTimer = Timer.periodic(reminderInterval, (_) {
      if (!_needsAttention) return; // Skip if already acknowledged
      _alerts.add(
        _Alert(
          DateTime.now(),
          'Reminder',
          'Check on occupant. Open the app to acknowledge.',
          isReminder: true,
        ),
      );
      setState(() {}); // Refresh the Alerts list
    });
  }

  // Stops reminders and logs an "Acknowledged" alert when the user opens the app.
  void _acknowledgeAttention() {
    if (!_needsAttention) return; // Nothing to do
    _needsAttention = false;
    _reminderTimer?.cancel();
    _reminderTimer = null;
    _alerts.add(
      _Alert(
        DateTime.now(),
        'Acknowledged',
        'Caregiver opened the app; reminders stopped.',
        isReminder: false,
      ),
    );
    setState(() {});
  }

  // ----------------------------------------------------------
  // GOTIFY EVENT HANDLERS
  // ----------------------------------------------------------

  // Called every time a new message arrives from the Gotify WebSocket.
  void _onGotifyMessage(Map<String, dynamic> msg) {
    // Extract the title/message from Gotify's JSON structure
    final title = (msg['title'] ?? 'Alert').toString();
    final body  = (msg['message'] ?? '').toString();

    // Add this as a new alert in the app and start reminders
    _alerts.add(_Alert(DateTime.now(), title, body, isReminder: false));
    _startReminders();
    setState(() {});

    // >>> OPTIONAL (commented out): also log falls to DB when Gotify says so.
    // If your payload contains a type/room/ts, you can insert here.
    // import 'package:drift/drift.dart' show Value;  // at top if you enable this
    //
    // final payload = msg; // or msg['payload'] if you wrap it
    // if ((payload['type'] ?? '').toString().toLowerCase() == 'fall') {
    //   final ts = payload['ts'];
    //   final occurredUtc = (ts is int)
    //       ? DateTime.fromMillisecondsSinceEpoch(ts * 1000, isUtc: true)
    //       : DateTime.now().toUtc();
    //   _fallDb.insertFall(FallEventsCompanion(
    //     occurredAtUtc: Value(occurredUtc),
    //     location: Value(payload['room']?.toString()),
    //     confidence: Value((payload['confidence'] is num)
    //         ? (payload['confidence'] as num).toDouble()
    //         : null),
    //     metaJson: Value(null),
    //   ));
    // }
  }

  // Called from the Settings page when the user taps "Save & Connect".
  void _saveGotifyConfig(String url, String token) {
    _serverUrl = url.trim();
    _appToken = token.trim();

    // Close any existing connection before opening a new one
    _gotify?.disconnect();

    if (_serverUrl.isNotEmpty && _appToken.isNotEmpty) {
      // Create a new Gotify service and start listening for messages
      _gotify = GotifyService(baseUrl: _serverUrl, appToken: _appToken);
      _gotify!.connect(_onGotifyMessage);

      // Confirmation message at bottom of screen
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Gotify connected (listening for messages).')),
      );
    } else {
      // User saved blank settings (disconnect)
      _gotify = null;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Gotify settings saved.')),
      );
    }
    setState(() {});
  }

  // ----------------------------------------------------------
  // MAIN UI BUILD (with 4 tabs: Home, Alerts, Log, Settings)
  // ----------------------------------------------------------
  @override
  Widget build(BuildContext context) {
    // Define the 4 main screens (tabs)
    final pages = [
      _Home( // Tab 0: Overview
        last: _last,
        needsAttention: _needsAttention,
        onAcknowledge: _acknowledgeAttention,
      ),
      _Alerts( // Tab 1: Alert history
        alerts: _alerts,
        onClear: () {
          setState(() {
            _alerts.clear();
          });
        },
      ),
      // >>> ADDED: Tab 2 — Caregiver Fall Log (weekly history)
      FallLogTab(externalDb: _fallDb),

      _Settings( // Tab 3: Settings form for Gotify
        serverUrl: _serverUrl,
        appToken: _appToken,
        onSave: _saveGotifyConfig,
      ),
    ];

    return Scaffold(
      appBar: AppBar(
        // >>> UPDATED: added "Log" to keep titles aligned with 4 tabs
        title: Text(['RADIAN', 'Alerts', 'Log', 'Settings'][_index]),
      ),
      body: pages[_index],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined),        label: 'Home'),
          NavigationDestination(icon: Icon(Icons.notifications_outlined), label: 'Alerts'),
          // >>> ADDED: new destination for the Fall Log tab
          NavigationDestination(icon: Icon(Icons.analytics_outlined),  label: 'Log'),
          NavigationDestination(icon: Icon(Icons.settings_outlined),    label: 'Settings'),
        ],
      ),
      // Floating action button is only visible on the Alerts tab
      floatingActionButton: _index == 1
          ? FloatingActionButton.extended(
        icon: const Icon(Icons.add_alert),
        label: const Text('Simulate Fall'),
        onPressed: _addInitialFallAlert,
      )
          : null,
    );
  }
}

// ----------------------------------------------------------
// HOME TAB
// ----------------------------------------------------------
// Displays current system status and a red banner if reminders are active.
class _Home extends StatelessWidget {
  final _Alert? last;             // Most recent alert
  final bool needsAttention;      // Whether reminders are active
  final VoidCallback onAcknowledge; // Called when user taps "Acknowledge"
  const _Home({
    required this.last,
    required this.needsAttention,
    required this.onAcknowledge,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    final isIdle = last == null && !needsAttention; // True if system idle

    return Padding(
      padding: const EdgeInsets.all(16),
      child: ListView(
        children: [
          // ----- Red banner while reminders are active -----
          if (needsAttention)
            Card(
              color: Colors.red.withValues(alpha: 0.12),
              child: ListTile(
                leading: const Icon(Icons.priority_high),
                title: const Text('Attention required'),
                subtitle: const Text('Periodic reminders are active until acknowledged.'),
                trailing: FilledButton(
                  onPressed: onAcknowledge,
                  child: const Text('Acknowledge'),
                ),
              ),
            ),
          const SizedBox(height: 12),

          // ----- System Status Card -----
          Card(
            clipBehavior: Clip.antiAlias,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('System Status', style: Theme.of(context).textTheme.titleLarge),
                  const SizedBox(height: 8),
                  // Status chip (Idle / Attention / Critical)
                  Chip(
                    avatar: Icon(isIdle ? Icons.check_circle : Icons.error, size: 18),
                    label: Text(isIdle ? 'Idle' : (needsAttention ? 'ATTENTION' : 'CRITICAL')),
                    side: BorderSide.none,
                    backgroundColor:
                    (isIdle ? Colors.teal : Colors.red).withValues(alpha: 0.15),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    last?.message ?? 'No recent activity.',
                    style: Theme.of(context).textTheme.bodyLarge,
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      const Icon(Icons.access_time, size: 16),
                      const SizedBox(width: 6),
                      Text(last == null ? '—' : _relative(last!.time)),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ----------------------------------------------------------
// ALERTS TAB
// ----------------------------------------------------------
// Shows a scrollable list of alerts and a Clear button.
class _Alerts extends StatelessWidget {
  final List<_Alert> alerts;
  final VoidCallback onClear;
  const _Alerts({required this.alerts, required this.onClear, super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Top row showing alert count + clear button
        if (alerts.isNotEmpty)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: Row(
              children: [
                Expanded(
                  child: Text('${alerts.length} alert${alerts.length == 1 ? '' : 's'} total'),
                ),
                TextButton.icon(
                  onPressed: onClear,
                  icon: const Icon(Icons.delete_outline),
                  label: const Text('Clear'),
                ),
              ],
            ),
          ),
        // List of alert cards (or placeholder if empty)
        Expanded(
          child: alerts.isEmpty
              ? const Center(child: Text('No alerts yet. Tap “Simulate Fall”.'))
              : ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: alerts.length,
            separatorBuilder: (_, __) => const SizedBox(height: 10),
            itemBuilder: (context, i) {
              final a = alerts[i];
              final tint = a.isReminder
                  ? Colors.red.withValues(alpha: 0.10)
                  : Colors.red.withValues(alpha: 0.15);
              return Card(
                color: tint,
                child: ListTile(
                  leading: Icon(
                    a.isReminder ? Icons.repeat : Icons.emergency_outlined,
                  ),
                  title: Text(a.title + (a.isReminder ? ' • Follow-up' : '')),
                  subtitle: Text('${_relative(a.time)} • ${a.message}'),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

// ----------------------------------------------------------
// SETTINGS TAB (with Gotify fields)
// ----------------------------------------------------------
// Lets the user enter a Gotify URL & token, and save/connect.
class _Settings extends StatefulWidget {
  final String serverUrl;                         // current URL (from _Root)
  final String appToken;                          // current token (from _Root)
  final void Function(String url, String token) onSave; // callback to save
  const _Settings({
    super.key,
    required this.serverUrl,
    required this.appToken,
    required this.onSave,
  });

  @override
  State<_Settings> createState() => _SettingsState();
}

class _SettingsState extends State<_Settings> {
  late final TextEditingController _urlCtrl;
  late final TextEditingController _tokenCtrl;

  @override
  void initState() {
    super.initState();
    // Preload existing values into the text fields
    _urlCtrl = TextEditingController(text: widget.serverUrl);
    _tokenCtrl = TextEditingController(text: widget.appToken);
  }

  @override
  void dispose() {
    _urlCtrl.dispose();
    _tokenCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Card for Gotify connection input fields
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Gotify Connection', style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 8),
                const Text('Enter your Gotify server address and app token below.'),
                const SizedBox(height: 12),
                // Server URL field
                TextField(
                  controller: _urlCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Server URL',
                    hintText: 'https://your-gotify-server:port',
                    prefixIcon: Icon(Icons.cloud_outlined),
                  ),
                  keyboardType: TextInputType.url,
                ),
                const SizedBox(height: 8),
                // App token field
                TextField(
                  controller: _tokenCtrl,
                  decoration: const InputDecoration(
                    labelText: 'App Token',
                    prefixIcon: Icon(Icons.vpn_key_outlined),
                  ),
                  obscureText: true, // hide token
                ),
                const SizedBox(height: 16),
                Align(
                  alignment: Alignment.centerRight,
                  child: FilledButton.icon(
                    icon: const Icon(Icons.save_outlined),
                    label: const Text('Save & Connect'),
                    onPressed: () {
                      // Pass values back to parent (_Root)
                      widget.onSave(_urlCtrl.text, _tokenCtrl.text);
                      FocusScope.of(context).unfocus(); // Close keyboard
                    },
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),
        // About card
        const Card(
          child: ListTile(
            leading: Icon(Icons.info_outline),
            title: Text('About RADIAN'),
            subtitle: Text('Prototype UI with periodic reminders.'),
          ),
        ),
      ],
    );
  }
}

// ----------------------------------------------------------
// DATA MODEL + TIME FORMATTER
// ----------------------------------------------------------
class _Alert {
  final DateTime time;     // timestamp of alert
  final String title;      // alert title (e.g., "FALL DETECTED")
  final String message;    // detailed description
  final bool isReminder;   // distinguishes follow-ups vs initial alerts
  _Alert(this.time, this.title, this.message, {this.isReminder = false});
}

// Helper: formats timestamps into "5m ago", "2h ago", etc.
String _relative(DateTime ts) {
  final d = DateTime.now().difference(ts);
  if (d.inSeconds < 60) return '${d.inSeconds}s ago';
  if (d.inMinutes < 60) return '${d.inMinutes}m ago';
  if (d.inHours < 24) return '${d.inHours}h ago';
  return '${d.inDays}d ago';
}
