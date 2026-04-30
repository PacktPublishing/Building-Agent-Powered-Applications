import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { EmailSummary } from '../types';

interface Props {
  summary: EmailSummary;
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default function EmailCard({ summary }: Props) {
  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.sender} numberOfLines={1}>
          {summary.sender}
        </Text>
        <Text style={styles.time}>{formatTime(summary.received_at)}</Text>
      </View>
      <Text style={styles.subject} numberOfLines={1}>
        {summary.subject}
      </Text>
      <Text style={styles.summary} numberOfLines={3}>
        {summary.summary}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 10,
    padding: 14,
    marginVertical: 5,
    marginHorizontal: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 3,
  },
  sender: {
    flex: 1,
    fontWeight: '600',
    fontSize: 14,
    color: '#111827',
  },
  time: {
    fontSize: 12,
    color: '#9CA3AF',
    marginLeft: 8,
  },
  subject: {
    fontSize: 13,
    fontWeight: '500',
    color: '#374151',
    marginBottom: 5,
  },
  summary: {
    fontSize: 13,
    color: '#6B7280',
    lineHeight: 19,
  },
});
