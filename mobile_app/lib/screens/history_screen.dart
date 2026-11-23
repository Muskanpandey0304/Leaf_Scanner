import 'dart:io';

import 'package:flutter/material.dart';

import '../app_state.dart';
import 'result_screen.dart';

class HistoryScreen extends StatefulWidget {
  final AppState state;
  const HistoryScreen({super.key, required this.state});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  String _stamp(DateTime t) {
    String two(int n) => n.toString().padLeft(2, '0');
    return '${t.year}-${two(t.month)}-${two(t.day)} ${two(t.hour)}:${two(t.minute)}';
  }

  @override
  Widget build(BuildContext context) {
    final items = widget.state.history.items;
    final kb = widget.state.kb;
    return Scaffold(
      appBar: AppBar(title: Text(widget.state.t('scan_history'))),
      body: items.isEmpty
          ? Center(child: Text(widget.state.t('no_scans')))
          : ListView.separated(
              itemCount: items.length,
              separatorBuilder: (_, __) => const Divider(height: 1),
              itemBuilder: (_, i) {
                final r = items[i];
                final top = r.top.first;
                final icon = r.feedback == 'yes'
                    ? const Icon(Icons.check_circle, color: Colors.green)
                    : r.feedback == 'no'
                        ? const Icon(Icons.cancel, color: Colors.red)
                        : const Icon(Icons.help_outline);
                return Dismissible(
                  key: ValueKey(r.id),
                  direction: DismissDirection.endToStart,
                  background: Container(
                    color: Colors.red,
                    alignment: Alignment.centerRight,
                    padding: const EdgeInsets.only(right: 20),
                    child: const Icon(Icons.delete, color: Colors.white),
                  ),
                  onDismissed: (_) async {
                    await widget.state.history.delete(r);
                    setState(() {});
                  },
                  child: ListTile(
                    leading: ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: Image.file(File(r.imagePath), width: 56, height: 56, fit: BoxFit.cover, cacheWidth: 112),
                    ),
                    title: Text(kb.of(top.id).kind == 'unknown' ? widget.state.t('not_sure_short') : kb.of(top.id).title),
                    subtitle: Text(kb.of(top.id).kind == 'unknown' ? _stamp(r.time) : '${kb.of(top.id).cropName}  -  ${(top.confidence * 100).round()}%  -  ${_stamp(r.time)}'),
                    trailing: icon,
                    onTap: () async {
                      await Navigator.of(context).push(MaterialPageRoute(
                        builder: (_) => ResultScreen(state: widget.state, record: r),
                      ));
                      setState(() {});
                    },
                  ),
                );
              },
            ),
    );
  }
}
