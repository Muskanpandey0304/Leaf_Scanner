import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../app_state.dart';
import '../strings.dart';
import 'history_screen.dart';
import 'result_screen.dart';

class HomeScreen extends StatefulWidget {
  final AppState state;
  const HomeScreen({super.key, required this.state});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _picker = ImagePicker();
  bool _busy = false;

  Future<void> _scan(ImageSource source) async {
    if (_busy) return;
    try {
      final picked = await _picker.pickImage(source: source, maxWidth: 1280, maxHeight: 1280, imageQuality: 92);
      if (picked == null) return;
      setState(() => _busy = true);
      final crop = widget.state.selectedCrop;
      final top = await widget.state.classifier.classify(picked.path,
          allowed: crop == null ? null : widget.state.kb.idsForCrop(crop));
      final rec = await widget.state.history.add(picked.path, top);
      if (!mounted) return;
      await Navigator.of(context).push(MaterialPageRoute(
        builder: (_) => ResultScreen(state: widget.state, record: rec),
      ));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(widget.state.t('went_wrong', {'e': '$e'}))));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _pickPlant() async {
    final crops = widget.state.kb.crops;
    final chosen = await showModalBottomSheet<String>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (ctx) => DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.7,
        builder: (_, ctrl) => ListView(controller: ctrl, children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 0, 20, 8),
            child: Text(widget.state.t('which_plant'), style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
          ),
          ListTile(
            leading: const Icon(Icons.auto_awesome_rounded),
            title: Text(widget.state.t('auto_detect')),
            subtitle: Text(widget.state.t('auto_sub')),
            selected: widget.state.selectedCrop == null,
            onTap: () => Navigator.pop(ctx, ''),
          ),
          for (final c in crops)
            ListTile(
              leading: const Icon(Icons.eco_outlined),
              title: Text(widget.state.kb.cropLabel(c)),
              selected: widget.state.selectedCrop == c,
              onTap: () => Navigator.pop(ctx, c),
            ),
        ]),
      ),
    );
    if (chosen == null) return;
    setState(() => widget.state.selectedCrop = chosen.isEmpty ? null : chosen);
  }

  void _about() {
    final crops = widget.state.kb.crops.map((c) => widget.state.kb.cropLabel(c)).toList();
    showDialog<void>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text(widget.state.t('about_title')),
        content: SingleChildScrollView(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
            Text(widget.state.t('supported_plants'), style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text(crops.join(', ')),
            const SizedBox(height: 12),
            Text(widget.state.t('about_body')),
            const SizedBox(height: 12),
            Text(widget.state.t('local_only')),
            const SizedBox(height: 12),
            Text(widget.state.t('mt_note'), style: const TextStyle(fontSize: 12)),
            const SizedBox(height: 12),
            const Text(
                'Non-commercial portfolio project. Trained on PlantVillage (CC BY-SA 3.0), PlantDoc (CC BY 4.0) '
                'and PlantWild (CC BY-NC-ND 4.0).',
                style: TextStyle(fontSize: 12)),
          ]),
        ),
        actions: [TextButton(onPressed: () => Navigator.pop(context), child: Text(widget.state.t('close')))],
      ),
    );
  }

  Widget _tip(IconData icon, String text) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(children: [
          Icon(icon, size: 20, color: Theme.of(context).colorScheme.primary),
          const SizedBox(width: 12),
          Expanded(child: Text(text)),
        ]),
      );

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Row(mainAxisAlignment: MainAxisAlignment.end, children: [
              PopupMenuButton<String>(
                tooltip: widget.state.t('language'),
                icon: const Icon(Icons.translate_rounded),
                initialValue: widget.state.lang,
                onSelected: (l) async {
                  await widget.state.setLang(l);
                  if (mounted) setState(() {});
                },
                itemBuilder: (_) => [
                  for (final e in Strings.languages.entries) PopupMenuItem(value: e.key, child: Text(e.value)),
                ],
              ),
              IconButton(
                tooltip: widget.state.t('history'),
                icon: const Icon(Icons.history_rounded),
                onPressed: () async {
                  await Navigator.of(context).push(MaterialPageRoute(builder: (_) => HistoryScreen(state: widget.state)));
                  if (mounted) setState(() {});
                },
              ),
              IconButton(tooltip: widget.state.t('about'), icon: const Icon(Icons.info_outline_rounded), onPressed: _about),
            ]),
            Container(
              padding: const EdgeInsets.symmetric(vertical: 30, horizontal: 20),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(28),
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [cs.primaryContainer, cs.secondaryContainer],
                ),
              ),
              child: Column(children: [
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(color: cs.surface.withAlpha(200), shape: BoxShape.circle),
                  child: Icon(Icons.eco_rounded, size: 52, color: cs.primary),
                ),
                const SizedBox(height: 16),
                Text('Leaf Scanner', style: tt.headlineMedium?.copyWith(fontWeight: FontWeight.w800)),
                const SizedBox(height: 6),
                Text(widget.state.t('tagline'),
                    textAlign: TextAlign.center, style: tt.bodyLarge),
              ]),
            ),
            const SizedBox(height: 22),
            SizedBox(
              height: 58,
              child: FilledButton.icon(
                style: FilledButton.styleFrom(shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18))),
                onPressed: _busy ? null : () => _scan(ImageSource.camera),
                icon: const Icon(Icons.photo_camera_rounded),
                label: Text(widget.state.t('take_photo'), style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600)),
              ),
            ),
            const SizedBox(height: 12),
            SizedBox(
              height: 54,
              child: OutlinedButton.icon(
                style: OutlinedButton.styleFrom(shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18))),
                onPressed: _busy ? null : () => _scan(ImageSource.gallery),
                icon: const Icon(Icons.photo_library_rounded),
                label: Text(widget.state.t('gallery'), style: const TextStyle(fontSize: 16)),
              ),
            ),
            const SizedBox(height: 12),
            Row(children: [
              Expanded(
                child: TextButton.icon(
                  onPressed: _busy ? null : _pickPlant,
                  icon: const Icon(Icons.local_florist_outlined),
                  label: Text(widget.state.selectedCrop == null
                      ? widget.state.t('choose_plant')
                      : widget.state.t('plant_n', {'p': widget.state.kb.cropLabel(widget.state.selectedCrop!)})),
                ),
              ),
              if (widget.state.selectedCrop != null)
                IconButton(
                  tooltip: widget.state.t('back_auto'),
                  icon: const Icon(Icons.close_rounded),
                  onPressed: _busy ? null : () => setState(() => widget.state.selectedCrop = null),
                ),
            ]),
            const SizedBox(height: 20),
            if (_busy)
              Column(children: [
                ClipRRect(borderRadius: BorderRadius.circular(6), child: const LinearProgressIndicator(minHeight: 6)),
                const SizedBox(height: 10),
                Text(widget.state.t('analysing')),
              ])
            else
              Card(
                elevation: 0,
                color: cs.surfaceContainerLow,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(widget.state.t('tips_title'), style: tt.titleSmall?.copyWith(fontWeight: FontWeight.w700)),
                    const SizedBox(height: 8),
                    _tip(Icons.crop_free_rounded, widget.state.t('tip1')),
                    _tip(Icons.wb_sunny_outlined, widget.state.t('tip2')),
                    _tip(Icons.block_rounded, widget.state.t('tip3')),
                  ]),
                ),
              ),
            const SizedBox(height: 18),
            Text(widget.state.t('scans_saved', {'n': '${widget.state.history.items.length}'}),
                textAlign: TextAlign.center, style: TextStyle(color: cs.outline)),
          ]),
        ),
      ),
    );
  }
}
