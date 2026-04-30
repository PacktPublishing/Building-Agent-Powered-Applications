import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import ReportView from '../components/ReportView';
import { reportApi } from '../services/api';
import { DailyReport } from '../types';

function recentDates(count: number): string[] {
  return Array.from({ length: count }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - i);
    return d.toISOString().split('T')[0];
  });
}

const TODAY = new Date().toISOString().split('T')[0];
const DATES = recentDates(14);

export default function ReportsScreen() {
  const [selectedDate, setSelectedDate] = useState(TODAY);
  const [report, setReport] = useState<DailyReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [notFound, setNotFound] = useState(false);

  const loadReport = useCallback(async (date: string) => {
    setLoading(true);
    setNotFound(false);
    try {
      setReport(await reportApi.getReportByDate(date));
    } catch {
      setReport(null);
      setNotFound(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadReport(selectedDate);
  }, [selectedDate, loadReport]);

  return (
    <View style={styles.container}>
      {/* Horizontal date picker */}
      <FlatList
        horizontal
        data={DATES}
        keyExtractor={(d) => d}
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.dateRow}
        renderItem={({ item }) => {
          const label = item === TODAY ? 'Today' : item.slice(5);
          const active = item === selectedDate;
          return (
            <TouchableOpacity
              style={[styles.chip, active && styles.chipActive]}
              onPress={() => setSelectedDate(item)}
            >
              <Text style={[styles.chipText, active && styles.chipTextActive]}>{label}</Text>
            </TouchableOpacity>
          );
        }}
      />

      {loading ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color="#2563EB" />
        </View>
      ) : notFound ? (
        <View style={styles.centered}>
          <Text style={styles.emptyText}>No report for {selectedDate}</Text>
        </View>
      ) : report ? (
        <ScrollView>
          <ReportView report={report} />
        </ScrollView>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  dateRow: { paddingHorizontal: 12, paddingVertical: 10 },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    marginHorizontal: 4,
    borderRadius: 20,
    backgroundColor: '#E5E7EB',
  },
  chipActive: { backgroundColor: '#2563EB' },
  chipText: { fontSize: 13, color: '#374151', fontWeight: '500' },
  chipTextActive: { color: '#fff' },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  emptyText: { color: '#9CA3AF', fontSize: 14 },
});
