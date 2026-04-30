import { Ionicons } from '@expo/vector-icons';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { NavigationContainer } from '@react-navigation/native';
import React from 'react';

import ChatScreen from '../screens/ChatScreen';
import HomeScreen from '../screens/HomeScreen';
import NotificationsScreen from '../screens/NotificationsScreen';
import ReportsScreen from '../screens/ReportsScreen';

const Tab = createBottomTabNavigator();

const ICON_MAP: Record<string, [string, string]> = {
  Home: ['home', 'home-outline'],
  Reports: ['document-text', 'document-text-outline'],
  Chat: ['chatbubble', 'chatbubble-outline'],
  Notifications: ['notifications', 'notifications-outline'],
};

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Tab.Navigator
        screenOptions={({ route }) => ({
          tabBarIcon: ({ focused, color, size }) => {
            const [active, inactive] = ICON_MAP[route.name] ?? ['help', 'help-outline'];
            return (
              <Ionicons
                name={(focused ? active : inactive) as React.ComponentProps<typeof Ionicons>['name']}
                size={size}
                color={color}
              />
            );
          },
          tabBarActiveTintColor: '#2563EB',
          tabBarInactiveTintColor: '#9CA3AF',
          headerStyle: { backgroundColor: '#2563EB' },
          headerTintColor: '#ffffff',
          headerTitleStyle: { fontWeight: '700' },
        })}
      >
        <Tab.Screen
          name="Home"
          component={HomeScreen}
          options={{ title: 'Email Agent' }}
        />
        <Tab.Screen name="Reports" component={ReportsScreen} />
        <Tab.Screen
          name="Chat"
          component={ChatScreen}
          options={{ title: 'Ask About Emails' }}
        />
        <Tab.Screen name="Notifications" component={NotificationsScreen} />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
