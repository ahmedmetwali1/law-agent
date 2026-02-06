# 🎨 التصور الفني الشامل لواجهة المستخدم
## Legal AI Assistant - Modern UI/UX Architecture

---

## 📐 المبادئ التصميمية الأساسية

### 1. Design Philosophy
```
"Intelligence Made Visible"
- إظهار قوة الذكاء الاصطناعي بشكل بصري
- الشفافية في عملية التفكير
- تجربة سلسة وسريعة الاستجابة
```

### 2. Visual Identity
- **نظام الألوان**: 
  - Primary: `#1E40AF` (أزرق قانوني محترف)
  - Secondary: `#059669` (أخضر للنجاح/الموافقة)
  - Warning: `#D97706` (برتقالي للتنبيهات)
  - Danger: `#DC2626` (أحمر للمخاطر)
  - Neutral: `#64748B` (رمادي للمعلومات)
  
- **الطباعة**: 
  - عربي: Cairo/Tajawal (واضح ومهني)
  - إنجليزي: Inter/Roboto (للكود والمصطلحات التقنية)

---

## 🏗️ هيكلية الواجهة (Layout Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                      Top Navigation Bar                      │
│  [Logo] [Workspace Name]         [Search] [Notifications] [@]│
└─────────────────────────────────────────────────────────────┘
┌──────────┬──────────────────────────────────┬───────────────┐
│          │                                  │               │
│          │      Main Chat Area              │   Inspector   │
│ Sidebar  │                                  │     Panel     │
│          │                                  │               │
│ - Chat   │  [Messages with AI reasoning]    │ - Context     │
│ - Cases  │                                  │ - Entities    │
│ - Docs   │                                  │ - Sources     │
│ - Tasks  │  ┌─────────────────────────────┐ │ - Confidence  │
│ - Team   │  │   Smart Input Area          │ │ - Tools Used  │
│          │  │ [Rich Text] [Attach] [Send] │ │               │
│          │  └─────────────────────────────┘ │               │
│          │                                  │               │
└──────────┴──────────────────────────────────┴───────────────┘
```

---

## 🎯 المكونات الرئيسية (Core Components)

### 1. Sidebar Navigator (القائمة الجانبية)

```typescript
// components/Sidebar/Sidebar.tsx

interface SidebarProps {
  activeWorkspace: string;
  onNavigate: (route: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ activeWorkspace, onNavigate }) => {
  const menuItems = [
    {
      icon: MessageSquare,
      label: 'المحادثات',
      route: '/chat',
      badge: 3, // عدد المحادثات الجديدة
      submenu: [
        { label: 'جميع الجلسات', route: '/chat/all' },
        { label: 'البحث القانوني', route: '/chat/research' },
        { label: 'صياغة العقود', route: '/chat/drafting' }
      ]
    },
    {
      icon: Briefcase,
      label: 'القضايا',
      route: '/cases',
      badge: null,
      submenu: [
        { label: 'قضايا نشطة', route: '/cases/active' },
        { label: 'قضايا منتهية', route: '/cases/closed' },
        { label: 'إنشاء قضية جديدة', route: '/cases/new' }
      ]
    },
    {
      icon: FileText,
      label: 'المستندات',
      route: '/documents',
      badge: null,
      submenu: [
        { label: 'عقود', route: '/documents/contracts' },
        { label: 'مذكرات', route: '/documents/memos' },
        { label: 'قوالب', route: '/documents/templates' }
      ]
    },
    {
      icon: CheckSquare,
      label: 'المهام',
      route: '/tasks',
      badge: 7,
      submenu: null
    },
    {
      icon: Users,
      label: 'الفريق',
      route: '/team',
      badge: null,
      submenu: null
    }
  ];

  return (
    <aside className="w-64 bg-slate-900 text-white border-r border-slate-800">
      {/* Header */}
      <div className="p-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
            <Scale className="w-6 h-6" />
          </div>
          <div>
            <h2 className="font-semibold">المستشار القانوني</h2>
            <p className="text-xs text-slate-400">{activeWorkspace}</p>
          </div>
        </div>
      </div>

      {/* Menu Items */}
      <nav className="p-2 space-y-1">
        {menuItems.map((item) => (
          <SidebarItem key={item.route} {...item} />
        ))}
      </nav>

      {/* Bottom Actions */}
      <div className="absolute bottom-0 w-64 p-4 border-t border-slate-800">
        <button className="w-full flex items-center gap-2 p-2 text-sm hover:bg-slate-800 rounded-lg">
          <Settings className="w-4 h-4" />
          <span>الإعدادات</span>
        </button>
      </div>
    </aside>
  );
};
```

---

### 2. Smart Chat Interface (واجهة المحادثة الذكية)

```typescript
// components/Chat/ChatInterface.tsx

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  metadata?: {
    category?: string;
    confidence?: number;
    reasoning?: string;
    tools_used?: string[];
    entities?: Entity[];
    sources?: Source[];
  };
  timestamp: Date;
  status?: 'sending' | 'sent' | 'error';
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [currentReasoning, setCurrentReasoning] = useState<string | null>(null);

  return (
    <div className="flex-1 flex flex-col bg-white">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((message) => (
          message.role === 'user' ? (
            <UserMessage key={message.id} message={message} />
          ) : (
            <AssistantMessage 
              key={message.id} 
              message={message}
              onReasoningClick={() => setCurrentReasoning(message.metadata?.reasoning)}
            />
          )
        ))}
        
        {/* AI Typing Indicator with Reasoning */}
        {isTyping && (
          <div className="space-y-3">
            <AIThinkingIndicator reasoning={currentReasoning} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <ChatInputArea onSend={handleSend} />
    </div>
  );
};

// User Message Component
const UserMessage: React.FC<{ message: Message }> = ({ message }) => (
  <div className="flex justify-end">
    <div className="max-w-2xl">
      <div className="bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-3">
        <p className="text-sm leading-relaxed">{message.content}</p>
      </div>
      <div className="flex items-center gap-2 mt-1 px-2 text-xs text-slate-500">
        <span>{format(message.timestamp, 'HH:mm')}</span>
        {message.status === 'sending' && <Loader className="w-3 h-3 animate-spin" />}
        {message.status === 'sent' && <Check className="w-3 h-3" />}
      </div>
    </div>
  </div>
);

// Assistant Message Component (المكون الأهم!)
const AssistantMessage: React.FC<{ 
  message: Message; 
  onReasoningClick: () => void 
}> = ({ message, onReasoningClick }) => {
  const [showSources, setShowSources] = useState(false);
  
  return (
    <div className="flex gap-3">
      {/* Avatar */}
      <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-full flex items-center justify-center flex-shrink-0">
        <Sparkles className="w-5 h-5 text-white" />
      </div>

      <div className="flex-1 space-y-3">
        {/* Category Badge */}
        <CategoryBadge 
          category={message.metadata?.category}
          confidence={message.metadata?.confidence}
        />

        {/* Main Content */}
        <div className="bg-slate-50 rounded-2xl rounded-tl-sm px-4 py-3 border border-slate-200">
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        </div>

        {/* Metadata Actions */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Reasoning Button */}
          {message.metadata?.reasoning && (
            <button
              onClick={onReasoningClick}
              className="text-xs flex items-center gap-1 px-3 py-1.5 bg-white border border-slate-200 rounded-full hover:bg-slate-50 transition-colors"
            >
              <Brain className="w-3 h-3" />
              <span>عرض التفكير المنطقي</span>
            </button>
          )}

          {/* Tools Used */}
          {message.metadata?.tools_used && message.metadata.tools_used.length > 0 && (
            <div className="text-xs flex items-center gap-1 px-3 py-1.5 bg-green-50 border border-green-200 rounded-full">
              <Wrench className="w-3 h-3 text-green-700" />
              <span className="text-green-700">
                استخدمت {message.metadata.tools_used.length} أداة
              </span>
            </div>
          )}

          {/* Sources */}
          {message.metadata?.sources && message.metadata.sources.length > 0 && (
            <button
              onClick={() => setShowSources(!showSources)}
              className="text-xs flex items-center gap-1 px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-full hover:bg-blue-100 transition-colors"
            >
              <BookOpen className="w-3 h-3 text-blue-700" />
              <span className="text-blue-700">
                {message.metadata.sources.length} مصدر قانوني
              </span>
            </button>
          )}

          {/* Entities */}
          {message.metadata?.entities && message.metadata.entities.length > 0 && (
            <EntitiesPill entities={message.metadata.entities} />
          )}

          {/* Timestamp */}
          <span className="text-xs text-slate-500 mr-auto">
            {format(message.timestamp, 'HH:mm')}
          </span>
        </div>

        {/* Expandable Sources */}
        {showSources && message.metadata?.sources && (
          <SourcesList sources={message.metadata.sources} />
        )}
      </div>
    </div>
  );
};
```

---

### 3. AI Thinking Indicator (مؤشر تفكير الذكاء الاصطناعي)

```typescript
// components/Chat/AIThinkingIndicator.tsx

interface AIThinkingIndicatorProps {
  reasoning: string | null;
}

const AIThinkingIndicator: React.FC<AIThinkingIndicatorProps> = ({ reasoning }) => {
  return (
    <div className="flex gap-3">
      <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-full flex items-center justify-center animate-pulse">
        <Sparkles className="w-5 h-5 text-white" />
      </div>

      <div className="flex-1 space-y-2">
        {/* Animated Thinking */}
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            <span className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
          <span className="text-sm text-slate-600 font-medium">المستشار يفكر...</span>
        </div>

        {/* Real-time Reasoning Display */}
        {reasoning && (
          <div className="bg-slate-50 border-l-4 border-blue-600 rounded-lg p-3 space-y-2">
            <div className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-blue-600" />
              <span className="text-xs font-semibold text-slate-700">التفكير المنطقي</span>
            </div>
            <p className="text-sm text-slate-600 leading-relaxed font-mono">
              {reasoning}
            </p>
          </div>
        )}

        {/* Processing Steps (optional) */}
        <div className="space-y-1">
          <ProcessingStep status="completed" text="تحليل الطلب" />
          <ProcessingStep status="active" text="البحث في قاعدة البيانات القانونية" />
          <ProcessingStep status="pending" text="صياغة الرد" />
        </div>
      </div>
    </div>
  );
};

const ProcessingStep: React.FC<{
  status: 'completed' | 'active' | 'pending';
  text: string;
}> = ({ status, text }) => {
  const icons = {
    completed: <CheckCircle className="w-4 h-4 text-green-600" />,
    active: <Loader className="w-4 h-4 text-blue-600 animate-spin" />,
    pending: <Circle className="w-4 h-4 text-slate-300" />
  };

  const colors = {
    completed: 'text-green-700',
    active: 'text-blue-700 font-medium',
    pending: 'text-slate-400'
  };

  return (
    <div className="flex items-center gap-2">
      {icons[status]}
      <span className={`text-xs ${colors[status]}`}>{text}</span>
    </div>
  );
};
```

---

### 4. Inspector Panel (لوحة التفتيش - الجانب الأيمن)

```typescript
// components/Chat/InspectorPanel.tsx

const InspectorPanel: React.FC<{ message: Message | null }> = ({ message }) => {
  if (!message) {
    return (
      <aside className="w-80 bg-slate-50 border-l border-slate-200 p-4">
        <div className="text-center text-slate-400 mt-20">
          <Info className="w-12 h-12 mx-auto mb-3" />
          <p className="text-sm">حدد رسالة لعرض التفاصيل</p>
        </div>
      </aside>
    );
  }

  return (
    <aside className="w-80 bg-slate-50 border-l border-slate-200 overflow-y-auto">
      <div className="p-4 space-y-6">
        {/* Confidence Meter */}
        <ConfidenceMeter 
          confidence={message.metadata?.confidence || 0}
          category={message.metadata?.category}
        />

        {/* Entities Detected */}
        {message.metadata?.entities && message.metadata.entities.length > 0 && (
          <InspectorSection title="الكيانات المستخرجة" icon={Tag}>
            <div className="space-y-2">
              {message.metadata.entities.map((entity, idx) => (
                <EntityCard key={idx} entity={entity} />
              ))}
            </div>
          </InspectorSection>
        )}

        {/* Tools Used */}
        {message.metadata?.tools_used && message.metadata.tools_used.length > 0 && (
          <InspectorSection title="الأدوات المستخدمة" icon={Wrench}>
            <div className="space-y-2">
              {message.metadata.tools_used.map((tool, idx) => (
                <ToolCard key={idx} toolName={tool} />
              ))}
            </div>
          </InspectorSection>
        )}

        {/* Legal Sources */}
        {message.metadata?.sources && message.metadata.sources.length > 0 && (
          <InspectorSection title="المصادر القانونية" icon={BookOpen}>
            <div className="space-y-2">
              {message.metadata.sources.map((source, idx) => (
                <SourceCard key={idx} source={source} />
              ))}
            </div>
          </InspectorSection>
        )}

        {/* Full Reasoning Trace */}
        {message.metadata?.reasoning && (
          <InspectorSection title="سلسلة التفكير الكاملة" icon={Brain}>
            <div className="bg-white rounded-lg p-3 border border-slate-200">
              <pre className="text-xs text-slate-700 font-mono whitespace-pre-wrap leading-relaxed">
                {message.metadata.reasoning}
              </pre>
            </div>
          </InspectorSection>
        )}

        {/* Context Used */}
        <InspectorSection title="السياق المستخدم" icon={FileText}>
          <div className="text-xs text-slate-600 space-y-1">
            <div className="flex justify-between">
              <span>عدد الرسائل السابقة:</span>
              <span className="font-semibold">5</span>
            </div>
            <div className="flex justify-between">
              <span>حجم السياق:</span>
              <span className="font-semibold">~2,340 tokens</span>
            </div>
          </div>
        </InspectorSection>
      </div>
    </aside>
  );
};

// Confidence Meter Component
const ConfidenceMeter: React.FC<{ 
  confidence: number; 
  category?: string 
}> = ({ confidence, category }) => {
  const percentage = Math.round(confidence * 100);
  const color = confidence > 0.8 ? 'green' : confidence > 0.5 ? 'yellow' : 'red';
  
  const colorClasses = {
    green: 'bg-green-500',
    yellow: 'bg-yellow-500',
    red: 'bg-red-500'
  };

  return (
    <div className="bg-white rounded-lg p-4 border border-slate-200">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-semibold text-slate-700">مستوى الثقة</span>
        <span className="text-2xl font-bold text-slate-900">{percentage}%</span>
      </div>
      
      {/* Progress Bar */}
      <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
        <div 
          className={`h-full ${colorClasses[color]} transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      {category && (
        <div className="mt-3 pt-3 border-t border-slate-200">
          <span className="text-xs text-slate-600">التصنيف:</span>
          <span className="text-xs font-semibold text-blue-600 mr-2">
            {category}
          </span>
        </div>
      )}
    </div>
  );
};

// Entity Card
const EntityCard: React.FC<{ entity: Entity }> = ({ entity }) => {
  const icons = {
    law: <Scale className="w-4 h-4" />,
    person: <User className="w-4 h-4" />,
    date: <Calendar className="w-4 h-4" />,
    money: <DollarSign className="w-4 h-4" />,
    location: <MapPin className="w-4 h-4" />
  };

  return (
    <div className="bg-white rounded-lg p-3 border border-slate-200 hover:border-blue-300 transition-colors cursor-pointer">
      <div className="flex items-start gap-2">
        <div className="text-blue-600 mt-0.5">
          {icons[entity.type as keyof typeof icons]}
        </div>
        <div className="flex-1">
          <div className="text-xs text-slate-500 mb-1">{entity.type}</div>
          <div className="text-sm font-medium text-slate-900">{entity.value}</div>
          {entity.article && (
            <div className="text-xs text-slate-600 mt-1">{entity.article}</div>
          )}
        </div>
      </div>
    </div>
  );
};
```

---

### 5. Smart Input Area (منطقة الإدخال الذكية)

```typescript
// components/Chat/ChatInputArea.tsx

const ChatInputArea: React.FC<{ onSend: (message: string, attachments?: File[]) => void }> = ({ onSend }) => {
  const [message, setMessage] = useState('');
  const [attachments, setAttachments] = useState<File[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Smart suggestions based on context
  const suggestions = [
    { icon: FileSearch, text: 'ابحث عن حكم قضائي', action: 'research' },
    { icon: FileEdit, text: 'اكتب عقد إيجار', action: 'draft' },
    { icon: Scale, text: 'حلل هذه القضية', action: 'analyze' },
    { icon: FileCheck, text: 'راجع هذه الوثيقة', action: 'review' }
  ];

  const handleSubmit = () => {
    if (!message.trim() && attachments.length === 0) return;
    onSend(message, attachments);
    setMessage('');
    setAttachments([]);
  };

  return (
    <div className="border-t border-slate-200 bg-white">
      {/* Attachments Preview */}
      {attachments.length > 0 && (
        <div className="px-6 pt-3 flex gap-2 flex-wrap">
          {attachments.map((file, idx) => (
            <AttachmentChip 
              key={idx} 
              file={file}
              onRemove={() => setAttachments(prev => prev.filter((_, i) => i !== idx))}
            />
          ))}
        </div>
      )}

      {/* Main Input */}
      <div className="p-4">
        <div className="flex items-end gap-3">
          {/* Attachment Button */}
          <button className="p-2 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
            <Paperclip className="w-5 h-5" />
          </button>

          {/* Textarea */}
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit();
                }
              }}
              placeholder="اكتب سؤالك القانوني هنا... (Shift+Enter للسطر الجديد)"
              className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none max-h-32"
              rows={1}
              style={{
                height: 'auto',
                minHeight: '48px'
              }}
            />

            {/* Suggestions Button */}
            <button
              onClick={() => setShowSuggestions(!showSuggestions)}
              className="absolute left-3 bottom-3 text-slate-400 hover:text-blue-600 transition-colors"
            >
              <Lightbulb className="w-5 h-5" />
            </button>
          </div>

          {/* Send Button */}
          <button
            onClick={handleSubmit}
            disabled={!message.trim() && attachments.length === 0}
            className="p-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>

        {/* Smart Suggestions */}
        {showSuggestions && (
          <div className="mt-3 grid grid-cols-2 gap-2">
            {suggestions.map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setMessage(suggestion.text);
                  setShowSuggestions(false);
                  textareaRef.current?.focus();
                }}
                className="flex items-center gap-2 p-3 text-sm text-left border border-slate-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors"
              >
                <suggestion.icon className="w-4 h-4 text-blue-600" />
                <span className="text-slate-700">{suggestion.text}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
```

---

### 6. Category Badge Component

```typescript
// components/Chat/CategoryBadge.tsx

const CategoryBadge: React.FC<{ 
  category?: string; 
  confidence?: number 
}> = ({ category, confidence }) => {
  if (!category) return null;

  const categoryConfig = {
    LEGAL_RESEARCH: { 
      label: 'بحث قانوني', 
      icon: FileSearch, 
      color: 'blue' 
    },
    CONTRACT_DRAFT: { 
      label: 'صياغة عقد', 
      icon: FileEdit, 
      color: 'purple' 
    },
    CASE_ANALYSIS: { 
      label: 'تحليل قضية', 
      icon: Scale, 
      color: 'indigo' 
    },
    LEGAL_ADVICE: { 
      label: 'استشارة قانونية', 
      icon: MessageCircle, 
      color: 'green' 
    },
    DOCUMENT_REVIEW: { 
      label: 'مراجعة وثيقة', 
      icon: FileCheck, 
      color: 'orange' 
    },
    COMPLIANCE_CHECK: { 
      label: 'فحص امتثال', 
      icon: Shield, 
      color: 'teal' 
    },
    CLIENT_INTAKE: { 
      label: 'استقبال عميل', 
      icon: UserPlus, 
      color: 'pink' 
    },
    ADMIN_TASK: { 
      label: 'مهمة إدارية', 
      icon: Briefcase, 
      color: 'gray' 
    },
    GENERAL_CHAT: { 
      label: 'محادثة عامة', 
      icon: MessageSquare, 
      color: 'slate' 
    }
  };

  const config = categoryConfig[category as keyof typeof categoryConfig] || categoryConfig.GENERAL_CHAT;
  const Icon = config.icon;

  const colorClasses = {
    blue: 'bg-blue-100 text-blue-700 border-blue-200',
    purple: 'bg-purple-100 text-purple-700 border-purple-200',
    indigo: 'bg-indigo-100 text-indigo-700 border-indigo-200',
    green: 'bg-green-100 text-green-700 border-green-200',
    orange: 'bg-orange-100 text-orange-700 border-orange-200',
    teal: 'bg-teal-100 text-teal-700 border-teal-200',
    pink: 'bg-pink-100 text-pink-700 border-pink-200',
    gray: 'bg-gray-100 text-gray-700 border-gray-200',
    slate: 'bg-slate-100 text-slate-700 border-slate-200'
  };

  return (
    <div className="flex items-center gap-2">
      <span className={`inline-flex items-center gap-1.5 px-3
# 📱 الصفحات المتخصصة والمكونات المتقدمة

---

## 🎯 7. Dashboard الرئيسي (Landing Page)

```typescript
// pages/Dashboard.tsx

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const { stats, recentCases, upcomingTasks } = useDashboardData();

  return (
    <div className="p-6 space-y-6">
      {/* Welcome Header */}
      <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl p-8 text-white">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">
              مرحباً، {user.name}
            </h1>
            <p className="text-blue-100">
              لديك {stats.activeCases} قضية نشطة و {stats.pendingTasks} مهمة معلقة
            </p>
          </div>
          <button className="bg-white/20 backdrop-blur-sm hover:bg-white/30 px-6 py-3 rounded-xl transition-colors flex items-center gap-2">
            <Plus className="w-5 h-5" />
            <span>محادثة جديدة</span>
          </button>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-4 gap-4 mt-8">
          <StatCard
            icon={MessageSquare}
            label="جلسات اليوم"
            value={stats.todaySessions}
            trend="+12%"
          />
          <StatCard
            icon={FileText}
            label="مستندات جديدة"
            value={stats.newDocuments}
            trend="+5%"
          />
          <StatCard
            icon={CheckCircle}
            label="مهام مكتملة"
            value={stats.completedTasks}
            trend="+8%"
          />
          <StatCard
            icon={TrendingUp}
            label="معدل الإنجاز"
            value={`${stats.completionRate}%`}
            trend="+3%"
          />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Recent Cases */}
        <div className="col-span-2">
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-slate-900">القضايا الأخيرة</h2>
              <button className="text-sm text-blue-600 hover:text-blue-700">
                عرض الكل
              </button>
            </div>
            <div className="space-y-4">
              {recentCases.map((case_) => (
                <CaseCard key={case_.id} case={case_} />
              ))}
            </div>
          </div>
        </div>

        {/* Upcoming Tasks */}
        <div>
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h2 className="text-xl font-bold text-slate-900 mb-6">المهام القادمة</h2>
            <div className="space-y-3">
              {upcomingTasks.map((task) => (
                <TaskCard key={task.id} task={task} />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* AI Assistant Quick Actions */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h2 className="text-xl font-bold text-slate-900 mb-6">
          ماذا يمكن للمستشار الذكي أن يساعدك؟
        </h2>
        <div className="grid grid-cols-4 gap-4">
          <QuickActionCard
            icon={FileSearch}
            title="بحث قانوني"
            description="ابحث في الأنظمة والأحكام"
            onClick={() => navigate('/chat?intent=research')}
          />
          <QuickActionCard
            icon={FileEdit}
            title="صياغة عقد"
            description="أنشئ عقد من قالب"
            onClick={() => navigate('/chat?intent=draft')}
          />
          <QuickActionCard
            icon={Scale}
            title="تحليل قضية"
            description="احصل على رأي قانوني"
            onClick={() => navigate('/chat?intent=analyze')}
          />
          <QuickActionCard
            icon={FileCheck}
            title="مراجعة وثيقة"
            description="فحص المخاطر والامتثال"
            onClick={() => navigate('/chat?intent=review')}
          />
        </div>
      </div>
    </div>
  );
};

const StatCard: React.FC<{
  icon: LucideIcon;
  label: string;
  value: string | number;
  trend: string;
}> = ({ icon: Icon, label, value, trend }) => (
  <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
    <div className="flex items-center justify-between mb-2">
      <Icon className="w-5 h-5 text-white/80" />
      <span className="text-xs text-green-300">{trend}</span>
    </div>
    <div className="text-2xl font-bold">{value}</div>
    <div className="text-sm text-blue-100">{label}</div>
  </div>
);
```

---

## 📄 8. صفحة القضايا (Cases Page)

```typescript
// pages/Cases.tsx

const CasesPage: React.FC = () => {
  const [view, setView] = useState<'grid' | 'list'>('grid');
  const [filter, setFilter] = useState<'all' | 'active' | 'closed'>('active');
  const { cases, isLoading } = useCases(filter);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">إدارة القضايا</h1>
          <p className="text-slate-600 mt-1">
            {cases.length} قضية {filter === 'active' ? 'نشطة' : filter === 'closed' ? 'منتهية' : 'إجمالي'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* View Toggle */}
          <div className="bg-white border border-slate-200 rounded-lg p-1 flex">
            <button
              onClick={() => setView('grid')}
              className={`p-2 rounded ${view === 'grid' ? 'bg-blue-100 text-blue-600' : 'text-slate-600'}`}
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setView('list')}
              className={`p-2 rounded ${view === 'list' ? 'bg-blue-100 text-blue-600' : 'text-slate-600'}`}
            >
              <List className="w-4 h-4" />
            </button>
          </div>

          {/* New Case Button */}
          <button className="bg-blue-600 text-white px-6 py-3 rounded-xl hover:bg-blue-700 transition-colors flex items-center gap-2">
            <Plus className="w-5 h-5" />
            <span>قضية جديدة</span>
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="flex bg-white border border-slate-200 rounded-lg p-1">
          <FilterTab
            active={filter === 'all'}
            onClick={() => setFilter('all')}
            label="الكل"
            count={cases.length}
          />
          <FilterTab
            active={filter === 'active'}
            onClick={() => setFilter('active')}
            label="نشطة"
            count={cases.filter(c => c.status === 'active').length}
          />
          <FilterTab
            active={filter === 'closed'}
            onClick={() => setFilter('closed')}
            label="منتهية"
            count={cases.filter(c => c.status === 'closed').length}
          />
        </div>

        {/* Search & Sort */}
        <div className="flex-1 flex items-center gap-3">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              placeholder="ابحث في القضايا..."
              className="w-full pr-10 pl-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <select className="px-4 py-3 border border-slate-200 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option>ترتيب: الأحدث</option>
            <option>ترتيب: الأقدم</option>
            <option>ترتيب: حسب الأولوية</option>
          </select>
        </div>
      </div>

      {/* Cases Grid/List */}
      {isLoading ? (
        <CasesLoading />
      ) : view === 'grid' ? (
        <div className="grid grid-cols-3 gap-6">
          {cases.map((case_) => (
            <CaseCardDetailed key={case_.id} case={case_} />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {cases.map((case_) => (
            <CaseListItem key={case_.id} case={case_} />
          ))}
        </div>
      )}
    </div>
  );
};

// Detailed Case Card for Grid View
const CaseCardDetailed: React.FC<{ case: Case }> = ({ case: case_ }) => {
  const statusColors = {
    active: 'bg-green-100 text-green-700 border-green-200',
    pending: 'bg-yellow-100 text-yellow-700 border-yellow-200',
    closed: 'bg-slate-100 text-slate-700 border-slate-200'
  };

  const priorityColors = {
    high: 'text-red-600',
    medium: 'text-orange-600',
    low: 'text-slate-600'
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 hover:border-blue-300 hover:shadow-lg transition-all cursor-pointer group">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className={`px-2 py-1 text-xs font-medium rounded-full border ${statusColors[case_.status]}`}>
              {case_.status === 'active' ? 'نشطة' : case_.status === 'pending' ? 'معلقة' : 'منتهية'}
            </span>
            <span className={`text-xs font-medium ${priorityColors[case_.priority]}`}>
              • {case_.priority === 'high' ? 'عالية' : case_.priority === 'medium' ? 'متوسطة' : 'منخفضة'}
            </span>
          </div>
          <h3 className="font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
            {case_.title}
          </h3>
          <p className="text-sm text-slate-600 mt-1 line-clamp-2">
            {case_.description}
          </p>
        </div>

        <button className="text-slate-400 hover:text-slate-600">
          <MoreVertical className="w-5 h-5" />
        </button>
      </div>

      {/* Client Info */}
      <div className="flex items-center gap-2 mb-4 pb-4 border-b border-slate-100">
        <User className="w-4 h-4 text-slate-400" />
        <span className="text-sm text-slate-600">{case_.clientName}</span>
      </div>

      {/* Metadata */}
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div>
          <span className="text-slate-500">رقم القضية:</span>
          <span className="font-medium text-slate-900 mr-1">
            {case_.caseNumber}
          </span>
        </div>
        <div>
          <span className="text-slate-500">المحكمة:</span>
          <span className="font-medium text-slate-900 mr-1">
            {case_.court}
          </span>
        </div>
        <div>
          <span className="text-slate-500">تاريخ البدء:</span>
          <span className="font-medium text-slate-900 mr-1">
            {format(case_.startDate, 'yyyy-MM-dd')}
          </span>
        </div>
        <div>
          <span className="text-slate-500">الجلسة القادمة:</span>
          <span className="font-medium text-slate-900 mr-1">
            {case_.nextHearing ? format(case_.nextHearing, 'yyyy-MM-dd') : 'غير محدد'}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 mt-4 pt-4 border-t border-slate-100">
        <button className="flex-1 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
          عرض التفاصيل
        </button>
        <button className="flex-1 py-2 text-sm text-slate-600 hover:bg-slate-50 rounded-lg transition-colors flex items-center justify-center gap-1">
          <MessageSquare className="w-4 h-4" />
          <span>محادثة</span>
        </button>
      </div>
    </div>
  );
};
```

---

## 📝 9. Document Viewer & Analyzer

```typescript
// components/Documents/DocumentAnalyzer.tsx

const DocumentAnalyzer: React.FC = () => {
  const [document, setDocument] = useState<File | null>(null);
  const [analysis, setAnalysis] = useState<DocumentAnalysis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleAnalyze = async () => {
    if (!document) return;
    
    setIsAnalyzing(true);
    // Call API to analyze document
    const result = await analyzeDocument(document);
    setAnalysis(result);
    setIsAnalyzing(false);
  };

  return (
    <div className="grid grid-cols-2 gap-6 h-full">
      {/* Document Viewer */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden flex flex-col">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <h3 className="font-semibold text-slate-900">الوثيقة</h3>
          {document && (
            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-slate-300 transition-colors flex items-center gap-2"
            >
              {isAnalyzing ? (
                <>
                  <Loader className="w-4 h-4 animate-spin" />
                  <span>جاري التحليل...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>تحليل الوثيقة</span>
                </>
              )}
            </button>
          )}
        </div>

        <div className="flex-1 overflow-auto">
          {!document ? (
            <DocumentUploader onUpload={setDocument} />
          ) : (
            <DocumentPreview document={document} />
          )}
        </div>
      </div>

      {/* Analysis Panel */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden flex flex-col">
        <div className="p-4 border-b border-slate-200">
          <h3 className="font-semibold text-slate-900">نتائج التحليل</h3>
        </div>

        <div className="flex-1 overflow-auto p-6">
          {!analysis ? (
            <div className="text-center text-slate-400 mt-20">
              <FileSearch className="w-16 h-16 mx-auto mb-4" />
              <p>قم برفع وثيقة لبدء التحليل</p>
            </div>
          ) : (
            <AnalysisResults analysis={analysis} />
          )}
        </div>
      </div>
    </div>
  );
};

const AnalysisResults: React.FC<{ analysis: DocumentAnalysis }> = ({ analysis }) => {
  return (
    <div className="space-y-6">
      {/* Summary */}
      <div>
        <h4 className="font-semibold text-slate-900 mb-3">ملخص الوثيقة</h4>
        <p className="text-sm text-slate-700 leading-relaxed">
          {analysis.summary}
        </p>
      </div>

      {/* Risk Assessment */}
      <div>
        <h4 className="font-semibold text-slate-900 mb-3">تقييم المخاطر</h4>
        <div className="space-y-3">
          {analysis.risks.map((risk, idx) => (
            <RiskItem key={idx} risk={risk} />
          ))}
        </div>
      </div>

      {/* Key Clauses */}
      <div>
        <h4 className="font-semibold text-slate-900 mb-3">البنود الرئيسية</h4>
        <div className="space-y-2">
          {analysis.keyClauses.map((clause, idx) => (
            <ClauseItem key={idx} clause={clause} />
          ))}
        </div>
      </div>

      {/* Missing Clauses */}
      {analysis.missingClauses.length > 0 && (
        <div>
          <h4 className="font-semibold text-slate-900 mb-3">بنود مفقودة</h4>
          <div className="space-y-2">
            {analysis.missingClauses.map((clause, idx) => (
              <div key={idx} className="flex items-start gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5" />
                <span className="text-sm text-yellow-800">{clause}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      <div>
        <h4 className="font-semibold text-slate-900 mb-3">التوصيات</h4>
        <div className="space-y-2">
          {analysis.recommendations.map((rec, idx) => (
            <div key={idx} className="flex items-start gap-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <Lightbulb className="w-4 h-4 text-blue-600 mt-0.5" />
              <span className="text-sm text-blue-800">{rec}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const RiskItem: React.FC<{ risk: Risk }> = ({ risk }) => {
  const severityColors = {
    high: 'bg-red-50 border-red-200 text-red-700',
    medium: 'bg-orange-50 border-orange-200 text-orange-700',
    low: 'bg-yellow-50 border-yellow-200 text-yellow-700'
  };

  const severityIcons = {
    high: XCircle,
    medium: AlertCircle,
    low: AlertTriangle
  };

  const Icon = severityIcons[risk.severity];

  return (
    <div className={`p-4 rounded-lg border ${severityColors[risk.severity]}`}>
      <div className="flex items-start gap-3">
        <Icon className="w-5 h-5 mt-0.5" />
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <h5 className="font-semibold">{risk.title}</h5>
            <span className="text-xs px-2 py-1 bg-white rounded-full">
              {risk.severity === 'high' ? 'عالي' : risk.severity === 'medium' ? 'متوسط' : 'منخفض'}
            </span>
          </div>
          <p className="text-sm mb-2">{risk.description}</p>
          <p className="text-xs opacity-75">
            <strong>الحل المقترح:</strong> {risk.solution}
          </p>
        </div>
      </div>
    </div>
  );
};
```

---

## ⚙️ 10. Settings & Configuration

```typescript
// pages/Settings.tsx

const SettingsPage: React.FC = () => {
  const tabs = [
    { id: 'profile', label: 'الملف الشخصي', icon: User },
    { id: 'ai', label: 'إعدادات الذكاء الاصطناعي', icon: Bot },
    { id: 'notifications', label: 'الإشعارات', icon: Bell },
    { id: 'security', label: 'الأمان', icon: Shield },
    { id: 'billing', label: 'الفواتير', icon: CreditCard }
  ];

  const [activeTab, setActiveTab] = useState('ai');

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold text-slate-900 mb-6">الإعدادات</h1>

      <div className="grid grid-cols-4 gap-6">
        {/* Tabs */}
        <div className="space-y-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-right ${
                  activeTab === tab.id
                    ? 'bg-blue-50 text-blue-700 font-medium'
                    : 'text-slate-600 hover:bg-slate-50'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Content */}
        <div className="col-span-3 bg-white rounded-xl border border-slate-200 p-6">
          {activeTab === 'ai' && <AISettings />}
          {activeTab === 'profile' && <ProfileSettings />}
          {activeTab === 'notifications' && <NotificationSettings />}
          {activeTab === 'security' && <SecuritySettings />}
          {activeTab === 'billing' && <BillingSettings />}
        </div>
      </div>
    </div>
  );
};

// AI Settings Component
const AISettings: React.FC = () => {
  const [settings, setSettings] = useState({
    model: 'gpt-4',
    temperature: 0.7,
    maxTokens: 2000,
    showReasoning: true,
    autoSummarize: true,
    confidenceThreshold: 0.8
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-900 mb-2">
          إعدادات الذكاء الاصطناعي
        </h2>
        <p className="text-sm text-slate-600">
          تخصيص سلوك المستشار القانوني الذكي
        </p>
      </div>

      {/* Model Selection */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-2">
          نموذج الذكاء الاصطناعي
        </label>
        <select
          value={settings.model}
          onChange={(e) => setSettings({ ...settings, model: e.target.value })}
          className="w-full px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="gpt-4">GPT-4 (الأكثر دقة)</option>
          <option value="gpt-3.5-turbo">GPT-3.5 Turbo (أسرع)</option>
          <option value="claude-3">Claude 3 Sonnet</option>
        </select>
      </div>

      {/* Temperature Slider */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-2">
          مستوى الإبداع (Temperature): {settings.temperature}
        </label>
        <input
          type="range"
          min="0"
          max="1"
          step="0.1"
          value={settings.temperature}
          onChange={(e) => setSettings({ ...settings, temperature: parseFloat(e.target.value) })}
          className="w-full"
        />
        <div className="flex justify-between text-xs text-slate-500 mt-1">
          <span>محافظ</span>
          <span>متوازن</span>
          <span>مبدع</span>
        </div>
      </div>

      {/* Max Tokens */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-2">
          الحد الأقصى للرد (Tokens)
        </label>
        <input
          type="number"
          value={settings.maxTokens}
          onChange={(e) => setSettings({ ...settings, maxTokens: parseInt(e.target.value) })}
          className="w-full px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Toggle Options */}
      <div className="space-y-4 pt-4 border-t border-slate-200">
        <ToggleSetting
          label="إظهار سلسلة التفكير (Reasoning)"
          description="عرض كيفية وصول الذكاء الاصطناعي للإجابة"
          checked={settings.showReasoning}
          onChange={(checked) => setSettings({ ...settings, showReasoning: checked })}
        />
        
        <ToggleSetting
          label="تلخيص تلقائي للمحادثات الطويلة"
          description="تلخيص المحادثات التي تتجاوز 10 رسائل تلقائياً"
          checked={settings.autoSummarize}
          onChange={(checked) => setSettings({ ...settings, autoSummarize: checked })}
        />
      </div>

      {/* Confidence Threshold */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-2">
          حد الثقة الأدنى: {(settings.confidenceThreshold * 100).toFixed(0)}%
        </label>
        <input
          type="range"
          min="0.5"
          max="1"
          step="0.05"
          value={settings.confidenceThreshold}
          onChange={(e) => setSettings({ ...settings, confidenceThreshold: parseFloat(e.target.value) })}
          className="w-full"
        />
        <p className="text-xs text-slate-500 mt-2">
          سيتم تحذيرك إذا كان مستوى ثقة الذكاء الاصطناعي أقل من هذا الحد
        </p>
      </div>

      {/* Save Button */}
      <div className="pt-4 border-t border-slate-200">
        <button className="bg-blue-600 text-white px-6 py-3 rounded-xl hover:bg-blue-700 transition-colors">
          حفظ التغييرات
        </button>
      </div>
    </div>
  );
};

const ToggleSetting: React.FC<{
  label: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}> = ({ label, description, checked, onChange }) => (
  <div className="flex items-start justify-between">
    <div className="flex-1">
      <div className="font-medium text-slate-900">{label}</div>
      <div className="text-sm text-slate-600 mt-1">{description}
