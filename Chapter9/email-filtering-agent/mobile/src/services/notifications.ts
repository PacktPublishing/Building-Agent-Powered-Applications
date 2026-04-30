import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';
import { deviceApi } from './api';

// Show alerts and play sound for all incoming notifications while the app is foregrounded.
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

/**
 * Request push notification permissions, obtain the Expo push token, and
 * register it with the backend.  Returns the token on success, null otherwise.
 */
export async function registerForPushNotifications(): Promise<string | null> {
  // Android requires a notification channel to be created before prompting.
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('urgent-emails', {
      name: 'Urgent Emails',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#FF2020',
    });
  }

  const { status: existing } = await Notifications.getPermissionsAsync();
  const finalStatus =
    existing === 'granted'
      ? existing
      : (await Notifications.requestPermissionsAsync()).status;

  if (finalStatus !== 'granted') {
    console.warn('[Notifications] Permission not granted.');
    return null;
  }

  const { data: token } = await Notifications.getExpoPushTokenAsync();
  await deviceApi.register(token);
  return token;
}

export function addNotificationListener(
  handler: (n: Notifications.Notification) => void,
): Notifications.Subscription {
  return Notifications.addNotificationReceivedListener(handler);
}

export function addResponseListener(
  handler: (r: Notifications.NotificationResponse) => void,
): Notifications.Subscription {
  return Notifications.addNotificationResponseReceivedListener(handler);
}
