// ===========================================================
// File: /lib/features/fall_log/fall_log_tab.dart
// Purpose: Caregiver "Fall Log" tab that displays weekly fall history.
// ===========================================================

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:radian/data/fall_db.dart';  // Import your database file
import 'week_utils.dart';                  // Import the helper for week ranges

class FallLogTab extends StatefulWidget {
  final FallDb? externalDb; // Optionally pass in a shared DB instance
  const FallLogTab({super.key, this.externalDb});

  @override
  State<FallLogTab> createState() => _FallLogTabState();
}

class _FallLogTabState extends State<FallLogTab> {
  late final FallDb _db;       // Local or shared database
  int weeksToShow = 26;        // How many past weeks to display (6 months)

  @override
  void initState() {
    super.initState();
    // If no external DB provided, create our own instance.
    _db = widget.externalDb ?? FallDb();
  }

  @override
  Widget build(BuildContext context) {
    final nowLocal = DateTime.now();                  // Current local time
    final currentWeekStartLocal = startOfWeekLocal(nowLocal); // Start of this week

    // Generate a list of week ranges (current + past)
    final weeks = List.generate(weeksToShow, (i) {
      final ws = currentWeekStartLocal.subtract(Duration(days: 7 * i));
      final we = endOfWeekLocal(ws);
      return (ws, we);
    });

    return Scaffold(
      appBar: AppBar(
        title: const Text('Fall Log'),
        centerTitle: true,
      ),

      // Scrollable list of week sections
      body: ListView.builder(
        itemCount: weeks.length,
        itemBuilder: (ctx, i) {
          final (wsLocal, weLocal) = weeks[i];
          final wsUtc = wsLocal.toUtc();
          final weUtc = weLocal.toUtc();
          final label = i == 0
              ? 'This Week (${weekLabel(wsLocal)})'
              : weekLabel(wsLocal);

          // Live query: automatically updates when new falls are added
          return StreamBuilder<List<FallEvent>>(
            stream: _db.watchFallsBetween(wsUtc, weUtc),
            builder: (ctx, snap) {
              final events = snap.data ?? const [];
              final count = events.length;

              return Card(
                margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),

                // Expandable section for each week
                child: ExpansionTile(
                  initiallyExpanded: i == 0, // Current week starts open
                  title: Row(
                    children: [
                      Text(label,
                          style: const TextStyle(fontWeight: FontWeight.w600)),
                      const Spacer(),
                      _CountPill(count: count), // Small badge showing # of falls
                    ],
                  ),

                  // Inner content: list of fall events
                  children: [
                    if (count == 0)
                      const Padding(
                        padding: EdgeInsets.all(16),
                        child: Text('No falls recorded.'),
                      )
                    else
                      ListView.separated(
                        physics: const NeverScrollableScrollPhysics(),
                        shrinkWrap: true,
                        itemCount: events.length,
                        separatorBuilder: (_, __) => const Divider(height: 1),
                        itemBuilder: (_, idx) {
                          final e = events[idx];
                          final local = e.occurredAtUtc.toLocal(); // Convert UTC → local
                          final tFmt = DateFormat('EEE, MMM d — h:mm a');
                          final subtitle = e.location?.isNotEmpty == true
                              ? '${tFmt.format(local)} · ${e.location}'
                              : tFmt.format(local);
                          final trailing = (e.confidence != null)
                              ? Text('${(e.confidence! * 100).toStringAsFixed(0)}%')
                              : const SizedBox.shrink();

                          // Single fall entry
                          return ListTile(
                            title: const Text('Fall detected'),
                            subtitle: Text(subtitle),
                            trailing: trailing,
                          );
                        },
                      ),
                    const SizedBox(height: 8),
                  ],
                ),
              );
            },
          );
        },
      ),
    );
  }
}

// -----------------------------------------------------------
// Small circular badge showing how many falls per week
// -----------------------------------------------------------
class _CountPill extends StatelessWidget {
  final int count;
  const _CountPill({required this.count});
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(999),
        color: Theme.of(context).colorScheme.primaryContainer,
      ),
      child: Text(
        '$count',
        style: TextStyle(color: Theme.of(context).colorScheme.onPrimaryContainer),
      ),
    );
  }
}
