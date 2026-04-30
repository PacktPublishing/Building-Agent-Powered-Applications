import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { DailyReport } from '../types';
import EmailCard from './EmailCard';

interface Props {
  report: DailyReport;
}

interface StatBadgeProps {
  label: string;
  count: number;
  bg: string;
  textColor?: string;
}

function StatBadge({ label, count, bg, textColor = '#1F2937' }: StatBadgeProps) {
  return (
    <View style={[styles.badge, { backgroundColor: bg }]}>
      <Text style={[styles.badgeCount, { color: textColor }]}>{count}</Text>
      <Text style={styles.badgeLabel}>{label}</Text>
    </View>
  );
}

export default function ReportView({ report }: Props) {
  return (
    <View>
      <Text style={styles.date}>{report.date}</Text>

      <View style={styles.statsRow}>
        <StatBadge label="Urgent" count={report.urgent_count} bg="#FEE2E2" textColor="#DC2626" />
        <StatBadge label="Important" count={report.important_count} bg="#DBEAFE" textColor="#1D4ED8" />
        <StatBadge label="Follow-ups" count={report.follow_up_count} bg="#FEF3C7" textColor="#B45309" />
        <StatBadge label="Ignored" count={report.ignored_count} bg="#F3F4F6" />
      </View>

      {report.summaries.length > 0 ? (
        <>
          <Text style={styles.sectionTitle}>Email Summaries</Text>
          {report.summaries.map((s) => (
            <EmailCard key={s.email_id} summary={s} />
          ))}
        </>
      ) : (
        <Text style={styles.empty}>No important emails summarized yet.</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  date: {
    fontSize: 17,
    fontWeight: '700',
    color: '#111827',
    textAlign: 'center',
    paddingVertical: 12,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: 12,
    paddingBottom: 8,
  },
  badge: {
    alignItems: 'center',
    borderRadius: 10,
    paddingVertical: 10,
    paddingHorizontal: 8,
    minWidth: 72,
  },
  badgeCount: {
    fontSize: 22,
    fontWeight: '700',
  },
  badgeLabel: {
    fontSize: 11,
    color: '#6B7280',
    marginTop: 2,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111827',
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 4,
  },
  empty: {
    textAlign: 'center',
    color: '#9CA3AF',
    fontSize: 14,
    marginTop: 40,
  },
});
