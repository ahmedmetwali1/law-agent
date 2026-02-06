# Mobile Backend API Reference
*Legal AI System v2.1 - Complete Mobile API Documentation*

---

## Version
- **Current Version:** v2.1.0  
- **Last Updated:** January 2026  
- **API Base URL:** `https://api.legal-ai.tech/v1` or your deployment URL  
- **Auth Scheme:** JWT Bearer Tokens  
- **Mobile-Only:** Yes (all endpoints mobile-optimized)

---

## Table of Contents
1. [Introduction](#1-introduction)
2. [Authentication & Security](#2-authentication--security)
3. [Rate Limits & Quotas](#3-rate-limits-quotas)
4. [Health & Monitoring](#4-health-monitoring)
5. [Cases](#5-cases)
6. [Client Management](#6-clients)
7. [Tasks & Calendar](#7-tasks--calendar)
8. [Documents & OCR](#8-documents-ocr-uploads)
9. [Chat with AI Agents](#9-ai-chat-assistant)
10. [Notifications](#10-notifications)
11. [Audit Logs](#11-audit-logs)
12. [Real-time Updates](#12-real-time-updates)
13. [Subscriptions](#13-subscriptions)
14. [Mobile Optimization](#14-mobile-optimization-guide)
15. [Error Handling](#15-error-handling)
16. [Code Examples](#16-code-examples)
17. [Mobile Push Notifications](#17-push-notifications)

---

## 1. Introduction

### **What This API Provides**
The Legal AI Mobile API powers the mobile app experience with real-time case management, AI-powered document analysis, and secure client data management. Built for performance with mobile-specific optimizations for offline-first operation.

### Key Mobile Features
- **Offline Sync**: Full offline support with conflict resolution
- **Real-time events**: WebSocket + push notifications for live updates
- **Zero-knowledge encryption**: Data encrypted end-to-end
- **Background sync**: Upload files when connection restored
- **Streaming AI Responses**: Server-sent events for AI agents

### Quick Start
```bash
# Authentication
curl -X POST https://api.legal-ai.tech/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@lawfirm.com","password":"••••••"}'

# Example response with tokens
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "def...",
  "expires_in": 86400,
  "user": { "id": "usr_123", "role": "lawyer" }
}
```

---

## 2. Authentication & Security

### 2.1 Authentication Flow

**Mobile Login Flow:**
1. Mobile app collects `email` and `password`
2. Send `POST /api/auth/login`
3. Receive tokens and user profile
4. Use token in subsequent requests:
   ```
   Authorization: Bearer {jwt_token}
   ```

**Login Request:**
```json
POST /api/auth/login
{
  "email": "ahmed@firm.com",
  "password": "SecurePass123!"
}
```

**Token Expiry & Refresh:**
- **Access Token**: Valid 24 hours
- **Refresh Token**: Valid 7 days, used to get new access token
- **Auto-refresh**: Send refresh token to `/api/auth/refresh`
- Mobile should refresh tokens when 