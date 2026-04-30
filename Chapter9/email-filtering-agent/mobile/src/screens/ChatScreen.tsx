import React, { useCallback, useRef, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { queryApi } from '../services/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  text: string;
}

const INTRO: Message = {
  id: '0',
  role: 'assistant',
  text: "Hi! Ask me anything about your emails. For example:\n• \"What urgent emails did I get today?\"\n• \"Summarize last week's activity.\"\n• \"Were there any follow-ups pending?\"",
};

export default function ChatScreen() {
  const [messages, setMessages] = useState<Message[]>([INTRO]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const listRef = useRef<FlatList>(null);

  const scrollToEnd = useCallback(() => {
    setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 80);
  }, []);

  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Message = { id: `${Date.now()}`, role: 'user', text };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    scrollToEnd();

    try {
      const res = await queryApi.ask(text, sessionId);
      setSessionId(res.session_id);
      setMessages((prev) => [
        ...prev,
        { id: `${Date.now() + 1}`, role: 'assistant', text: res.answer },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `${Date.now() + 1}`,
          role: 'assistant',
          text: 'Sorry, something went wrong. Please check your connection and try again.',
        },
      ]);
    } finally {
      setLoading(false);
      scrollToEnd();
    }
  }, [input, loading, sessionId, scrollToEnd]);

  const renderMessage = ({ item }: { item: Message }) => {
    const isUser = item.role === 'user';
    return (
      <View style={[styles.bubble, isUser ? styles.userBubble : styles.botBubble]}>
        <Text style={[styles.bubbleText, isUser ? styles.userText : styles.botText]}>
          {item.text}
        </Text>
      </View>
    );
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={92}
    >
      <FlatList
        ref={listRef}
        data={messages}
        keyExtractor={(m) => m.id}
        renderItem={renderMessage}
        contentContainerStyle={styles.list}
        onContentSizeChange={scrollToEnd}
      />

      {loading && (
        <View style={styles.typing}>
          <ActivityIndicator size="small" color="#2563EB" />
          <Text style={styles.typingText}>Thinking…</Text>
        </View>
      )}

      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="Ask about your emails…"
          multiline
          maxLength={500}
          returnKeyType="send"
          blurOnSubmit={false}
          onSubmitEditing={send}
        />
        <TouchableOpacity
          style={[styles.sendBtn, (!input.trim() || loading) && styles.sendBtnOff]}
          onPress={send}
          disabled={!input.trim() || loading}
        >
          <Text style={styles.sendText}>Send</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  list: { padding: 14, paddingBottom: 6 },
  bubble: {
    maxWidth: '82%',
    borderRadius: 16,
    padding: 12,
    marginVertical: 4,
  },
  userBubble: { alignSelf: 'flex-end', backgroundColor: '#2563EB' },
  botBubble: {
    alignSelf: 'flex-start',
    backgroundColor: '#ffffff',
    shadowColor: '#000',
    shadowOpacity: 0.07,
    shadowRadius: 3,
    shadowOffset: { width: 0, height: 1 },
    elevation: 1,
  },
  bubbleText: { fontSize: 14, lineHeight: 20 },
  userText: { color: '#ffffff' },
  botText: { color: '#111827' },
  typing: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 6,
  },
  typingText: { marginLeft: 8, color: '#9CA3AF', fontSize: 13 },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 10,
    backgroundColor: '#ffffff',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 9,
    fontSize: 14,
    maxHeight: 100,
    backgroundColor: '#F9FAFB',
  },
  sendBtn: {
    marginLeft: 8,
    backgroundColor: '#2563EB',
    borderRadius: 20,
    paddingHorizontal: 18,
    paddingVertical: 10,
  },
  sendBtnOff: { backgroundColor: '#93C5FD' },
  sendText: { color: '#ffffff', fontWeight: '700', fontSize: 14 },
});
