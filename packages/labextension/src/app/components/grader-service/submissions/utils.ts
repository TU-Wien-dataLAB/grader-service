import { SubmissionRow } from './submissions-data-table';
import { Submission } from '../../../../model/submission';

const toRow = (s: Submission, label?: string): SubmissionRow => ({
  id: String(s.id),
  studentName: s.user_display_name ?? '',
  label,
  score: s.score,
  gradingStatus: s.auto_status,
  feedbackStatus: s.feedback_status,
  submission: s
});

export const toSubmissionRows = (
  submissions: Array<Submission> | null
): Array<SubmissionRow> => {
  const byUser = new Map<number | undefined, Array<Submission>>();
  (submissions || []).forEach(s => {
    byUser.set(s.user_id, [...(byUser.get(s.user_id) ?? []), s]);
  });

  return [...byUser.entries()].map(([userId, list]) => {
    if (list.length === 1) return toRow(list[0]);

    const sorted = [...list].sort((a, b) =>
      (a.submitted_at ?? '').localeCompare(b.submitted_at ?? '')
    );
    return {
      id: `user-${userId}`,
      studentName: sorted[0].user_display_name ?? '',
      subRows: sorted.map((s, i) => toRow(s, `Submission ${i + 1}`)).reverse()
    };
  });
};

const pad = (n: number) => String(n).padStart(2, '0');

export const formatSubmittedAt = (iso?: string) => {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.${d.getFullYear()} ${pad(
    d.getHours()
  )}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
};
