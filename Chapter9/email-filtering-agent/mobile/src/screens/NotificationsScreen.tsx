import * as Notifications from 'expo-notifications';
import React, { useCallback, useEffect, useState } from 'react';
import {
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { UrgentNotification } from '../types';

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function NotificationsScreen() {
  const [notifications, setNotifications] = useState<UrgentNotification[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const loadNotifications = useCallback(async () => {
    const delivered = await Notifications.getPresentedNotificationsAsync();
    const urgent: UrgentNotification[] = delivered
      .filter((n) => n.request.content.data?.type === 'urgent_email')
      .map((n) => ({
        id: n.request.identifier,
        subject: (n.request.content.title ?? 'Unknown').replace(/^Urgent:\s*/i, ''),
        sender: (n.request.content.body ?? 'Unknown').replace(/^From:\s*/i, ''),
        email_id: (n.request.content.data?.email_id as string) ?? '',
        received_at: new Date().toISOString(),
      }));
    setNotifications(urgent);
  }, []);

  useEffect(() => {
    loadNotifications();
    const sub = Notifications.addNotificationReceivedListener(loadNotifications);
    return () => sub.remove();
  }, [loadNotifications]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadNotifications();
    setRefreshing(false);
  }, [loadNotifications]);

  const renderItem = ({ item }: { item: UrgentNotification }) => (
    <View style={styles.card}>
      <View style={styles.badge}>
        <Text style={styles.badgeText}>URGENT</Text>
      </View>
      <Text style={styles.subject}>{item.subject}</Text>
      <Text style={styles.meta}>From: {item.sender}</Text>
      <Text style={styles.meta}>{formatDate(item.received_at)}</Text>
    </View>
  );

  return (
    <FlatList
      style={styles.container}
      data={notifications}
      keyExtractor={(n) => n.id}
      renderItem={renderItem}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      contentContainerStyle={notifications.length === 0 ? styles.emptyContainer : undefined}
      ListEmptyComponent={
        <View style={styles.emptyWrap}>
          <Text style={styles.emptyTitle}>No Urgent Notifications</Text>
          <Text style={styles.emptyText}>
            Urgent emails will appear here when the agent escalates them.
          </Text>
        </View>
      }
    />
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 10,
    padding: 16,
    marginVertical: 6,
    marginHorizontal: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#DC2626',
    shadowColor: '#000',
    shadowOpacity: 0.07,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 1 },
    elevation: 2,
  },
  badge: {
    alignSelf: 'flex-start',
    backgroundColor: '#FEE2E2',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    marginBottom: 8,
  },
  badgeText: { color: '#DC2626', fontSize: 11, fontWeight: '700', letterSpacing: 0.5 },
  subject: { fontSize: 15, fontWeight: '600', color: '#111827', marginBottom: 4 },
  meta: { fontSize: 13, color: '#6B7280' },
  emptyContainer: { flex: 1 },
  emptyWrap: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingTop: 120, paddingHorizontal: 32 },
  emptyTitle: { fontSize: 18, fontWeight: '600', color: '#374151', marginBottom: 8 },
  emptyText: { fontSize: 14, color: '#9CA3AF', textAlign: 'center', lineHeight: 20 },
});
