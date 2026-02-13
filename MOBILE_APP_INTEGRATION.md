# Mobile App Integration Guide

## Overview

The EzMsg Protocol API provides a complete REST API for integrating the QuitTxt smoking cessation protocol into your mobile application. This guide shows you how to use the API to guide users through the protocol flow.

## Live API

**Base URL:** `http://localhost:8000/v1` (or your deployed API base URL)
**API Key:** `YOUR_PROTOCOL_API_KEY`
**Project ID:** `1` (QuitTxt V9 UTSA Study)

## Authentication

All API requests require an API key in the header:

```http
X-API-Key: YOUR_PROTOCOL_API_KEY
Content-Type: application/json
```

## API Endpoints

### 1. Start Protocol Session

**Endpoint:** `POST /protocol/start`

Start a new protocol session for a user.

**Request:**
```json
{
  "project_id": 1,
  "language": "en",  // "en" or "es"
  "initial_response": null  // Optional: "iquit0" for immediate quit
}
```

**Response:**
```json
{
  "session_id": "30de3080-8550-46fc-8c48-b204b49b3f1a",
  "project_id": 1,
  "project_name": "QuitTxt V9 UTSA Study",
  "current_node_id": 1,
  "current_node_name": "INTAKE_START",
  "message": {
    "message_text": "Welcome to Quitxt from the UT Health Science Center...",
    "media_url": "https://youtu.be/F_NhIMsHBf8",
    "quick_replies": [],
    "expects_reply": false,
    "is_terminal": false
  },
  "session_time": "2026-01-21T07:22:17.716311",
  "next_scheduled_at": null
}
```

**cURL Example:**
```bash
curl -X POST https://gregarious-vitality-production.up.railway.app/v1/protocol/start \
  -H "X-API-Key: YOUR_PROTOCOL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "language": "en"
  }'
```

### 2. Send User Response

**Endpoint:** `POST /protocol/respond`

Send a user's response to continue the protocol flow.

**Request:**
```json
{
  "session_id": "30de3080-8550-46fc-8c48-b204b49b3f1a",
  "response": "YES_TOMORROW"
}
```

**Response:** Same structure as `/protocol/start`

**cURL Example:**
```bash
curl -X POST https://gregarious-vitality-production.up.railway.app/v1/protocol/respond \
  -H "X-API-Key: YOUR_PROTOCOL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "30de3080-8550-46fc-8c48-b204b49b3f1a",
    "response": "1"
  }'
```

### 3. Get Session Status

**Endpoint:** `GET /protocol/session/{session_id}`

Check the current status of a session.

**Response:**
```json
{
  "session_id": "30de3080-8550-46fc-8c48-b204b49b3f1a",
  "project_id": 1,
  "current_node_id": 14,
  "language": "en",
  "current_time": "2026-01-21T07:36:17.000000",
  "created_at": "2026-01-21T07:22:17.716311"
}
```

**cURL Example:**
```bash
curl https://gregarious-vitality-production.up.railway.app/v1/protocol/session/30de3080-8550-46fc-8c48-b204b49b3f1a \
  -H "X-API-Key: YOUR_PROTOCOL_API_KEY"
```

### 4. End Session

**Endpoint:** `DELETE /protocol/session/{session_id}`

End and delete a session.

**Response:**
```json
{
  "status": "deleted",
  "session_id": "30de3080-8550-46fc-8c48-b204b49b3f1a"
}
```

**cURL Example:**
```bash
curl -X DELETE https://gregarious-vitality-production.up.railway.app/v1/protocol/session/30de3080-8550-46fc-8c48-b204b49b3f1a \
  -H "X-API-Key: YOUR_PROTOCOL_API_KEY"
```

## Integration Flow

### 1. Initialize Session

When a user wants to start the quit smoking protocol:

```typescript
// Mobile App (TypeScript/React Native example)
const API_BASE_URL = 'http://localhost:8000/v1'; // or your deployed API base URL
const PROTOCOL_API_KEY = 'YOUR_PROTOCOL_API_KEY'; // store securely

const startProtocol = async (language: 'en' | 'es') => {
  const response = await fetch(
    `${API_BASE_URL}/protocol/start`,
    {
      method: 'POST',
      headers: {
        'X-API-Key': PROTOCOL_API_KEY,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        project_id: 1,
        language: language,
      }),
    }
  );

  const data = await response.json();

  // Store session_id for future requests
  await AsyncStorage.setItem('protocol_session_id', data.session_id);

  // Display the message to user
  displayMessage(data.message);

  return data;
};
```

### 2. Display Messages

Show the message content to the user:

```typescript
const displayMessage = (message: ProtocolMessage) => {
  // Display message text
  setMessageText(message.message_text);

  // Display media if available
  if (message.media_url) {
    setMediaUrl(message.media_url);
  }

  // Show quick reply buttons if available
  if (message.quick_replies && message.quick_replies.length > 0) {
    setQuickReplies(message.quick_replies);
  }

  // Check if we expect a response
  setExpectsReply(message.expects_reply);

  // Check if protocol is complete
  if (message.is_terminal) {
    handleProtocolComplete();
  }
};
```

### 3. Handle User Responses

When user selects an option or types a response:

```typescript
const sendUserResponse = async (response: string) => {
  const sessionId = await AsyncStorage.getItem('protocol_session_id');

  const res = await fetch(
    `${API_BASE_URL}/protocol/respond`,
    {
      method: 'POST',
      headers: {
        'X-API-Key': PROTOCOL_API_KEY,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        response: response,
      }),
    }
  );

  const data = await res.json();

  // Display next message
  displayMessage(data.message);

  return data;
};
```

### 4. Handle Scheduled Messages

The API provides `next_scheduled_at` to tell you when the next message should be shown:

```typescript
const scheduleNextMessage = (nextScheduledAt: string) => {
  const nextTime = new Date(nextScheduledAt);
  const now = new Date();
  const delayMs = nextTime.getTime() - now.getTime();

  if (delayMs > 0) {
    // Schedule a notification
    scheduleNotification({
      title: 'QuitTxt Message',
      body: 'You have a new message waiting!',
      trigger: { seconds: delayMs / 1000 },
    });
  }
};
```

## Complete React Native Example

```typescript
import React, { useState, useEffect } from 'react';
import { View, Text, Button, Image } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE = 'http://localhost:8000/v1'; // or your deployed API base URL
const API_KEY = 'YOUR_PROTOCOL_API_KEY'; // store securely
const PROJECT_ID = 1;

interface ProtocolMessage {
  message_text: string;
  media_url?: string;
  quick_replies: Array<{ label: string; value: string }>;
  expects_reply: boolean;
  is_terminal: boolean;
}

interface SessionResponse {
  session_id: string;
  message: ProtocolMessage;
  next_scheduled_at?: string;
}

export const ProtocolScreen = () => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [message, setMessage] = useState<ProtocolMessage | null>(null);
  const [loading, setLoading] = useState(false);

  const startProtocol = async (language: 'en' | 'es') => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/protocol/start`, {
        method: 'POST',
        headers: {
          'X-API-Key': API_KEY,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          project_id: PROJECT_ID,
          language,
        }),
      });

      const data: SessionResponse = await response.json();
      setSessionId(data.session_id);
      setMessage(data.message);

      await AsyncStorage.setItem('protocol_session_id', data.session_id);
    } catch (error) {
      console.error('Error starting protocol:', error);
    } finally {
      setLoading(false);
    }
  };

  const sendResponse = async (responseValue: string) => {
    if (!sessionId) return;

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/protocol/respond`, {
        method: 'POST',
        headers: {
          'X-API-Key': API_KEY,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          response: responseValue,
        }),
      });

      const data: SessionResponse = await response.json();
      setMessage(data.message);

      if (data.next_scheduled_at) {
        // Schedule notification for next message
        scheduleNotification(data.next_scheduled_at);
      }
    } catch (error) {
      console.error('Error sending response:', error);
    } finally {
      setLoading(false);
    }
  };

  const scheduleNotification = (scheduledTime: string) => {
    // Implement notification scheduling
    console.log('Schedule notification for:', scheduledTime);
  };

  return (
    <View style={{ padding: 20 }}>
      {!sessionId && (
        <>
          <Button title="Start (English)" onPress={() => startProtocol('en')} />
          <Button title="Empezar (Español)" onPress={() => startProtocol('es')} />
        </>
      )}

      {message && (
        <View>
          <Text style={{ fontSize: 16, marginVertical: 20 }}>
            {message.message_text}
          </Text>

          {message.media_url && (
            <Image
              source={{ uri: message.media_url }}
              style={{ width: '100%', height: 200 }}
              resizeMode="contain"
            />
          )}

          {message.quick_replies.map((qr) => (
            <Button
              key={qr.value}
              title={qr.label}
              onPress={() => sendResponse(qr.value)}
              disabled={loading}
            />
          ))}

          {message.is_terminal && (
            <Text style={{ color: 'green', marginTop: 20 }}>
              Protocol complete
            </Text>
          )}
        </View>
      )}

      {loading && <Text>Loading...</Text>}
    </View>
  );
};
```

## Flutter/Dart Example

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ProtocolAPI {
  static const String baseUrl =
    'http://localhost:8000/v1'; // or your deployed API base URL
  static const String apiKey = 'YOUR_PROTOCOL_API_KEY'; // store securely
  static const int projectId = 1;

  static Future<Map<String, dynamic>> startProtocol(String language) async {
    final response = await http.post(
      Uri.parse('$baseUrl/protocol/start'),
      headers: {
        'X-API-Key': apiKey,
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'project_id': projectId,
        'language': language,
      }),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);

      // Store session ID
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('session_id', data['session_id']);

      return data;
    } else {
      throw Exception('Failed to start protocol');
    }
  }

  static Future<Map<String, dynamic>> sendResponse(String responseValue) async {
    final prefs = await SharedPreferences.getInstance();
    final sessionId = prefs.getString('session_id');

    final response = await http.post(
      Uri.parse('$baseUrl/protocol/respond'),
      headers: {
        'X-API-Key': apiKey,
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'session_id': sessionId,
        'response': responseValue,
      }),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to send response');
    }
  }
}
```

## Swift/iOS Example

```swift
import Foundation

class ProtocolAPI {
    static let baseURL = "http://localhost:8000/v1" // or your deployed API base URL
    static let apiKey = "YOUR_PROTOCOL_API_KEY" // store securely
    static let projectId = 1

    static func startProtocol(language: String, completion: @escaping (Result<[String: Any], Error>) -> Void) {
        let url = URL(string: "\(baseURL)/protocol/start")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "project_id": projectId,
            "language": language
        ]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }

            guard let data = data,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
                completion(.failure(NSError(domain: "", code: -1)))
                return
            }

            // Store session ID
            if let sessionId = json["session_id"] as? String {
                UserDefaults.standard.set(sessionId, forKey: "session_id")
            }

            completion(.success(json))
        }.resume()
    }

    static func sendResponse(response: String, completion: @escaping (Result<[String: Any], Error>) -> Void) {
        guard let sessionId = UserDefaults.standard.string(forKey: "session_id") else {
            completion(.failure(NSError(domain: "No session ID", code: -1)))
            return
        }

        let url = URL(string: "\(baseURL)/protocol/respond")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "session_id": sessionId,
            "response": response
        ]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }

            guard let data = data,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
                completion(.failure(NSError(domain: "", code: -1)))
                return
            }

            completion(.success(json))
        }.resume()
    }
}
```

## Testing the API

Run the included test script to see the complete flow:

```bash
cd api
source venv/bin/activate
python test_protocol_api_flow.py
```

This will demonstrate:
- Starting a session
- Progressing through multiple messages
- Handling quick replies
- Managing session state
- Testing Spanish language
- Testing "iquit0" shortcut

## Key Response Fields

| Field | Description | Mobile App Usage |
|-------|-------------|------------------|
| `session_id` | Unique session identifier | Store for all subsequent requests |
| `message.message_text` | Message content | Display to user |
| `message.media_url` | YouTube link or image URL | Show in WebView or Image component |
| `message.quick_replies` | Array of button options | Render as buttons |
| `message.expects_reply` | Whether user response needed | Show/hide input UI |
| `message.is_terminal` | End of protocol | Show completion screen |
| `next_scheduled_at` | When next message should appear | Schedule push notification |

## Protocol Features

### Bilingual Support

The protocol supports English and Spanish:

```json
{
  "language": "en"  // English
}

{
  "language": "es"  // Spanish (Español)
}
```

All messages, quick replies, and media are localized.

### Shortcuts

- **`iquit0`**: Fast-track to immediate quit flow (skips some intake questions)

```json
{
  "project_id": 1,
  "language": "en",
  "initial_response": "iquit0"
}
```

### Quick Replies

When `message.quick_replies` is populated, display as buttons:

```json
{
  "quick_replies": [
    { "label": "Yes, let's do it!", "value": "YES_TOMORROW" },
    { "label": "No, not yet", "value": "NEED_TIME" }
  ]
}
```

Send the `value` field in your response.

## Error Handling

```typescript
try {
  const response = await fetch(url, options);

  if (!response.ok) {
    const error = await response.json();
    console.error('API Error:', error.detail);

    // Handle specific errors
    if (response.status === 401) {
      // Invalid API key
    } else if (response.status === 404) {
      // Session not found or expired
    } else if (response.status === 400) {
      // Protocol ended or invalid request
    }
  }

  return await response.json();
} catch (error) {
  console.error('Network error:', error);
}
```

## Production Considerations

1. **Session Persistence**: Store `session_id` in secure storage (Keychain/Keystore)
2. **Offline Support**: Queue responses and send when back online
3. **Push Notifications**: Use `next_scheduled_at` to schedule local/push notifications
4. **Error Recovery**: Handle session expiration gracefully (restart protocol)
5. **Analytics**: Track message views, response times, completion rates
6. **Media Caching**: Cache YouTube thumbnails and images for better UX

## Support

For questions or issues with the API:
- Check the test script: `api/test_protocol_api_flow.py`
- Review the API implementation: `api/app/routers/protocol_api.py`
- Test in the web dashboard: https://shiny-pancake-production.up.railway.app/admin

## Protocol Content

The QuitTxt V9 protocol includes:
- **63 messaging nodes**: Complete workflow from intake to quit day support
- **61 message templates**: Bilingual (EN/ES) with YouTube video links
- **Timing elements**: From immediate to daily scheduled messages
- **Keywords**: EXIT, HELP, HELPNOW for user-initiated actions
- **Variables**: Track quit_date, preferred_time, progress metrics

Estimated protocol duration: 21+ days of daily support messages
