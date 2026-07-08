import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../recruitment_provider.dart';

class ApplicantsScreen extends StatefulWidget {
  final String postId;

  const ApplicantsScreen({super.key, required this.postId});

  @override
  State<ApplicantsScreen> createState() => _ApplicantsScreenState();
}

class _ApplicantsScreenState extends State<ApplicantsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<RecruitmentProvider>().fetchApplicants(widget.postId);
    });
  }

  @override
  Widget build(BuildContext context) {
    final recruitment = context.watch<RecruitmentProvider>();

    return Scaffold(
      appBar: AppBar(title: const Text('Applicants')),
      body: _buildBody(recruitment),
    );
  }

  Widget _buildBody(RecruitmentProvider recruitment) {
    if (recruitment.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (recruitment.error != null) {
      return Center(child: Text(recruitment.error!));
    }

    final applicants = recruitment.applicants;
    if (applicants.isEmpty) {
      return const Center(child: Text('No applicants yet.'));
    }

    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: applicants.length,
      separatorBuilder: (_, _) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final applicant = applicants[index];
        final isPending = (applicant['status'] ?? 'PENDING') == 'PENDING';

        return Card(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  applicant['player_email'] ?? 'Unknown player',
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                Text(applicant['player_message'] ?? 'No message'),
                const SizedBox(height: 8),
                Text('Status: ${applicant['status'] ?? 'PENDING'}'),
                if (applicant['contact'] != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 6),
                    child: Text('Contact: ${applicant['contact']}'),
                  ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton.icon(
                        onPressed: isPending
                            ? () async {
                                final ok = await context
                                    .read<RecruitmentProvider>()
                                    .updateApplicationStatus(
                                      applicant['id'],
                                      'ACCEPTED',
                                    );
                                if (ok && mounted) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(
                                      content: Text('Application accepted.'),
                                    ),
                                  );
                                }
                              }
                            : null,
                        icon: const Icon(Icons.check),
                        label: const Text('Accept'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: isPending
                            ? () async {
                                final ok = await context
                                    .read<RecruitmentProvider>()
                                    .updateApplicationStatus(
                                      applicant['id'],
                                      'REJECTED',
                                    );
                                if (ok && mounted) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(
                                      content: Text('Application rejected.'),
                                    ),
                                  );
                                }
                              }
                            : null,
                        icon: const Icon(Icons.close),
                        label: const Text('Reject'),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
