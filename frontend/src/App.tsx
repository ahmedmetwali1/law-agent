import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { BreadcrumbProvider } from './contexts/BreadcrumbContext'
import { Toaster } from 'sonner'
import { LoginPage } from './pages/auth/LoginPage'
import { SignupPage } from './pages/SignupPage'
import { ClientsPage as Clients } from './pages/Clients'
import { ClientProfile } from './pages/ClientProfile'
import { KnowledgeBasePage } from './pages/KnowledgeBasePage'
import { CasesPage } from './pages/CasesPage'
import { CaseDetails } from './pages/CaseDetails'
import Hearings from './pages/Hearings'
import { AssistantsPage } from './pages/AssistantsPage'
import { TasksPage } from './pages/TasksPage'
import { AuditLogPage } from './pages/AuditLogPage'
import { PoliceRecordsPage } from './pages/PoliceRecordsPage'
import { SettingsPage } from './pages/SettingsPage'
import { PrivacyPage } from './pages/PrivacyPage'
import { AboutPage } from './pages/AboutPage'
import { ConceptPage } from './pages/ConceptPage'
import { SubscriptionsPage } from './pages/SubscriptionsPage'
import { SupportPage } from './pages/SupportPage'

import { AIPage } from './pages/AIPage'
import { Dashboard } from './pages/Dashboard'
import { ChatPage } from './pages/ChatPage'
import { AppShell } from './components/layout/AppShell'
import { RequireAuth } from './components/auth/RequireAuth'

function App() {
    return (
        <BrowserRouter>
            <Toaster
                position="top-center"
                richColors
                dir="rtl"
                toastOptions={{
                    style: {
                        fontFamily: "'Ruqaa', 'Cairo', sans-serif",
                        direction: 'rtl'
                    }
                }}
            />
            <AuthProvider>
                <BreadcrumbProvider>
                    <Routes>
                        {/* Public Routes */}
                        <Route path="/login" element={<LoginPage />} />
                        <Route path="/signup" element={<SignupPage />} />

                        {/* Redirect root to login */}
                        <Route path="/" element={<Navigate to="/login" replace />} />

                        {/* Protected Routes - Wrapped with RequireAuth */}
                        <Route element={<RequireAuth />}>
                            <Route element={<AppShell />}>
                                {/* Nested routes inside AppShell */}
                                <Route index element={<Navigate to="/dashboard" replace />} />
                                <Route path="dashboard" element={<Dashboard />} />
                                <Route path="chat" element={<ChatPage />} />
                                <Route path="clients" element={<Clients />} />
                                <Route path="clients/:id" element={<ClientProfile />} />
                                <Route path="cases" element={<CasesPage />} />
                                <Route path="cases/:id" element={<CaseDetails />} />
                                <Route path="hearings" element={<Hearings />} />
                                <Route path="assistants" element={<AssistantsPage />} />
                                <Route path="tasks" element={<TasksPage />} />
                                <Route path="audit-log" element={<AuditLogPage />} />
                                <Route path="ai" element={<AIPage />} />
                                <Route path="reports" element={<PoliceRecordsPage />} />
                                <Route path="documents" element={<div className="glass-card p-6"><h1 className="text-2xl font-bold">المستندات</h1></div>} />
                                <Route path="knowledge" element={<KnowledgeBasePage />} />
                                <Route path="settings" element={<SettingsPage />} />
                                <Route path="privacy" element={<PrivacyPage />} />
                                <Route path="about" element={<AboutPage />} />
                                <Route path="idea" element={<ConceptPage />} />
                                <Route path="subscriptions" element={<SubscriptionsPage />} />
                                <Route path="support" element={<SupportPage />} />
                            </Route>
                        </Route>
                    </Routes>
                </BreadcrumbProvider>
            </AuthProvider>
        </BrowserRouter>
    )
}

export default App
