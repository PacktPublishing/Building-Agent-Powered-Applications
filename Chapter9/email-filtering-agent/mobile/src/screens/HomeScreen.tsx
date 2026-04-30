import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import ReportView from '../components/ReportView';
import { reportApi } from '../services/api';
import { DailyReport } from '../types';

export default function HomeScreen() {
  const [report, setReport] = useState<DailyReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadReport = useCallback(async () => {
    try {
      setError(null);
      setReport(await reportApi.getTodayReport());
    } catch {
      setError("Couldn't load today's report. Is the backend running?");
    }
  }, []);

  useEffect(() => {
    loadReport().finally(() => setLoading(false));
  }, [loadReport]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadReport();
    setRefreshing(false);
  }, [loadReport]);

  const handleFinalize = async () => {
    try {
      setReport(await reportApi.finalizeReport());
    } catch {
      setError('Failed to finalize report.');
    }
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#2563EB" />
        <Text style={styles.loadingText}>Loading today's report…</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {error && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      <View style={styles.titleRow}>
        <Text style={styles.title}>Today's Overview</Text>
        {report && !report.finalized && (
          <TouchableOpacity style={styles.finalizeBtn} onPress={handleFinalize}>
            <Text style={styles.finalizeBtnText}>Finalize</Text>
          </TouchableOpacity>
        )}
        {report?.finalized && (
          <View style={styles.finalizedBadge}>
            <Text style={styles.finalizedText}>✓ Finalized</Text>
          </View>
        )}
      </View>

      {report && <ReportView report={report} />}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  loadingText: { marginTop: 12, color: '#6B7280', fontSize: 14 },
  errorBox: {
    margin: 16,
    padding: 12,
    backgroundColor: '#FEE2E2',
    borderRadius: 8,
  },
  errorText: { color: '#DC2626', fontSize: 13 },
  titleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 16,
  },
  title: { fontSize: 20, fontWeight: '700', color: '#111827' },
  finalizeBtn: {
    backgroundColor: '#2563EB',
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 8,
  },
  finalizeBtnText: { color: '#fff', fontWeight: '600', fontSize: 13 },
  finalizedBadge: {
    backgroundColor: '#D1FAE5',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
  },
  finalizedText: { color: '#065F46', fontWeight: '600', fontSize: 12 },
});
