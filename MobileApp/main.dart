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
import 'dart:convert';  // for jsonEncode
import 'package:drift/drift.dart' show Value; // for Drift companions

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
  ThemeMode _themeMode = ThemeMode.light; // default to system theme (light mode)

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
      _themeMode = savedIndex == 1 ? ThemeMode.dark : ThemeMode.light;
    });
  }

  // Save theme choice and apply immediately
  Future<void> _setTheme(ThemeMode mode) async {
    final prefs = await SharedPreferences.getInstance();
    final value = mode == ThemeMode.dark ? 1 : 0;
    await prefs.setInt('themeMode', value);
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

      home: _Root(
        themeMode: _themeMode,
        onThemeChanged: _setTheme,
      ),
    );
  }
}

// ----------------------------------------------------------
// MAIN STATEFUL SHELL (_Root)
// ----------------------------------------------------------
// Handles navigation (bottom tabs), reminders, alerts, theme, and Gotify state.
class _Root extends StatefulWidget {
  const _Root({
    super.key,
    required this.themeMode,
    required this.onThemeChanged,
  });

  final ThemeMode themeMode;
  final ValueChanged<ThemeMode> onThemeChanged;

  @override
  State<_Root> createState() => _RootState();
}

class _RootState extends State<_Root> with WidgetsBindingObserver {
  bool _gotifyConnected = false;
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
  _Alert? get _last => _alerts.isEmpty ? null : _alerts.first;

  // -------------------------------
  // GOTIFY CONNECTION VARIABLES
  // -------------------------------
  String _serverUrl = '';         // User-entered Gotify server URL
  String _clientToken = '';          // User-entered Gotify app token
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
  /*
  void _addInitialFallAlert() {
    _alerts.insert(0,
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
  */

  // ----------------------------------------------------------
  // REMINDER HANDLING
  // ----------------------------------------------------------
  // Starts a repeating timer that adds a "Reminder" alert every 30 seconds.
  void _startReminders() {
    _needsAttention = true;
    _reminderTimer?.cancel(); // Prevent overlapping timers
    _reminderTimer = Timer.periodic(reminderInterval, (_) {
      if (!_needsAttention) return; // Skip if already acknowledged
      _alerts.insert(0,
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
    _alerts.insert(0,
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
  Future<void> _onGotifyMessage(Map<String, dynamic> msg) async {
    final title = (msg['title'] ?? 'Alert').toString();
    final body  = (msg['message'] ?? '').toString();

    _alerts.insert(0, _Alert(DateTime.now(), title, body, isReminder: false));

    final s = ('$title $body').toLowerCase();
    final priority = (msg['priority'] is num) ? (msg['priority'] as num).toInt() : 0;
    final isFall = s.contains('fall') || priority >= 8;

    if (isFall) {
      _startReminders();

      try {
        await _fallDb.insertFall(
          FallEventsCompanion.insert(
            occurredAtUtc: DateTime.now().toUtc(),
            source: const Value('gotify'),
            metaJson: Value(jsonEncode(msg)),
          ),
        );
      } catch (e, st) {
        debugPrint('[FALL_LOG] insert FAILED: $e');
        debugPrint('$st');
      }
    }

    setState(() {});
  }

  // Called from the Settings page when the user taps "Save & Connect".
  void _saveGotifyConfig(String url, String token) {
    _serverUrl = url.trim();
    _clientToken = token.trim();

    // Close any existing connection before opening a new one
    _gotify?.disconnect();
    setState(() => _gotifyConnected = false);

    if (_serverUrl.isNotEmpty && _clientToken.isNotEmpty) {
      // Create a new Gotify service and start listening for messages
      _gotify = GotifyService(baseUrl: _serverUrl, clientToken: _clientToken);
      _gotify!.connect(
          _onGotifyMessage,
          onStatus: (connected) {
            if (!mounted) return;
            setState(() => _gotifyConnected = connected);
          },
      );

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
        isConnected: _gotifyConnected,
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
        clientToken: _clientToken,
        isConnected: _gotifyConnected,
        onSave: _saveGotifyConfig,
        themeMode: widget.themeMode,
        onThemeChanged: widget.onThemeChanged,
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
    );
  }
}

// ----------------------------------------------------------
// HOME TAB
// ----------------------------------------------------------
// Displays current system status and a red banner if reminders are active.
class _Home extends StatelessWidget {
  final _Alert? last;
  final bool needsAttention;
  final bool isConnected;
  final VoidCallback onAcknowledge;

  const _Home({
    required this.last,
    required this.needsAttention,
    required this.isConnected,
    required this.onAcknowledge,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    final systemColor = isConnected ? Colors.green : Colors.orange;
    final monitoringColor = needsAttention ? Colors.red : Colors.green;
    final monitoringText = needsAttention ? 'Attention Required' : 'Monitoring';

    return Padding(
      padding: const EdgeInsets.all(16),
      child: ListView(
        children: [
          if (needsAttention)
            Card(
              color: Colors.red.withValues(alpha: 0.12),
              child: ListTile(
                leading: const Icon(Icons.priority_high),
                title: const Text('Attention required'),
                subtitle: const Text(
                  'Periodic reminders are active until acknowledged',
                ),
                trailing: FilledButton(
                  onPressed: onAcknowledge,
                  child: const Text('Acknowledge'),
                ),
              ),
            ),

          const SizedBox(height: 12),

          Card(
            child: ListTile(
              leading: Icon(Icons.cloud_done_outlined, color: systemColor),
              title: const Text('System Status'),
              subtitle: Text(
                isConnected ? 'Connected to Gotify' : 'Not connected to Gotify',
              ),
            ),
          ),

          const SizedBox(height: 12),

          Card(
            child: ListTile(
              leading: Icon(Icons.sensors_outlined, color: monitoringColor),
              title: const Text('Monitoring Status'),
              subtitle: Text(monitoringText),
            ),
          ),

          const SizedBox(height: 12),

          Card(
            child: ListTile(
              leading: const Icon(Icons.notifications_active_outlined),
              title: const Text('Last Alert'),
              subtitle: last == null
                  ? const Text('No alerts yet')
                  : Text('${last!.title} • ${_relative(last!.time)}'),
            ),
          ),

          const SizedBox(height: 12),

          const Card(
            child: ListTile(
              leading: Icon(Icons.analytics_outlined),
              title: Text('Fall Log'),
              subtitle: Text('Recent fall events are saved in the Log tab.'),
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
              ? const Center(child: Text('No alerts yet. Waiting for Gotify messages...'))
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
  final String clientToken;                          // current token (from _Root)
  final void Function(String url, String token) onSave; // callback to save
  final ThemeMode themeMode;
  final ValueChanged<ThemeMode> onThemeChanged;
  final bool isConnected;

  const _Settings({
    super.key,
    required this.serverUrl,
    required this.clientToken,
    required this.onSave,
    required this.themeMode,
    required this.onThemeChanged,
    required this.isConnected,
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
    _tokenCtrl = TextEditingController(text: widget.clientToken);
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
        // Card for Gotify connection input fields (collapses when connected)
        Card(
          child: ExpansionTile(
            initiallyExpanded: !widget.isConnected,
            leading: Icon(
              widget.isConnected ? Icons.check_circle : Icons.cloud_outlined,
              color: widget.isConnected ? Colors.green : null,
            ),
            title: const Text('Gotify Connection'),
            subtitle: Text(widget.isConnected ? 'Connected' : 'Not connected'),
            children: [
              Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Enter your Gotify server address and client token below.'),
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

                    // Client token field
                    TextField(
                      controller: _tokenCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Client Token',
                        prefixIcon: Icon(Icons.vpn_key_outlined),
                      ),
                      obscureText: true,
                    ),
                    const SizedBox(height: 16),

                    Align(
                      alignment: Alignment.centerRight,
                      child: FilledButton.icon(
                        icon: const Icon(Icons.save_outlined),
                        label: const Text('Save & Connect'),
                        onPressed: () {
                          widget.onSave(_urlCtrl.text, _tokenCtrl.text);
                          FocusScope.of(context).unfocus();
                        },
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 12),

        Card(
          child: Padding(
            padding: const EdgeInsets.all(8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const ListTile(
                  leading: Icon(Icons.brightness_6_outlined),
                  title: Text('Theme'),
                  subtitle: Text('Choose light or dark mode.'),
                ),
                RadioListTile<ThemeMode>(
                  title: const Text('Light'),
                  value: ThemeMode.light,
                  groupValue: widget.themeMode,
                  onChanged: (mode) {
                    if (mode != null) widget.onThemeChanged(mode);
                  },
                ),
                RadioListTile<ThemeMode>(
                  title: const Text('Dark'),
                  value: ThemeMode.dark,
                  groupValue: widget.themeMode,
                  onChanged: (mode) {
                    if (mode != null) widget.onThemeChanged(mode);
                  },
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
            subtitle: Text('Real-time radar-based fall detection system with mobile alerts and event logging for caregiver monitoring.'),
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
