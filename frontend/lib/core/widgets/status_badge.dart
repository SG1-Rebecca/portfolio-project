import 'package:flutter/material.dart';
import 'package:frontend/core/enums.dart';

class StatusBadge extends StatelessWidget {
  final ApplicationStatus appStatus;

  const StatusBadge({super.key, required this.appStatus});

  @override
  Widget build(BuildContext context) {
    final (color, label) = switch (appStatus) {
      ApplicationStatus.pending => (Colors.orange, 'Pending'),
      ApplicationStatus.accepted => (Colors.green, 'Accepted'),
      ApplicationStatus.rejected => (Colors.red, 'Rejected'),
      ApplicationStatus.withdrawn => (Colors.grey, 'Withdrawn'),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: 12,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }
}
