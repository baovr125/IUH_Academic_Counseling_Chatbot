# IUH Portal AI — Frontend Scaffold

React + Vite + TypeScript + Tailwind. UI is fully mocked; every mock service
call goes through the exact `ApiResult<T>` shape the FastAPI backend will
return, so swapping a mock for `fetch(...)` never touches a component.

## Run it

```bash
npm install
npm run dev
```

## Folder structure

```
src/
├── types/
│   └── index.ts              # API contracts (User, ChatMessage, Citation, ...)
│
├── mock/
│   └── mockData.ts           # Fixtures: users, sessions, translations, flashcards
│
├── services/                 # ⚠️ Only layer that "talks" to a backend.
│   ├── utils.ts               #   delay()/generateId() helpers for mocks
│   ├── authService.ts         #   login / register / logout
│   ├── chatService.ts         #   RAG chat: fetchSessions, sendMessage
│   ├── translationService.ts  #   translateText, history CRUD
│   ├── dashboardService.ts    #   fetchDashboardStats
│   └── flashcardService.ts    #   fetchFlashcardSet, rateFlashcard
│
├── hooks/                     # State + orchestration, no JSX.
│   ├── useAuth.ts              #   Context-based auth state
│   ├── useChat.ts              #   ⭐ sample hook — sessions, messages, isSending
│   ├── useTranslation.ts
│   ├── useDashboard.ts
│   └── useFlashcards.ts
│
├── components/
│   ├── layout/                #   Sidebar, TopBar, MainLayout (<Outlet/>)
│   └── chat/                  #   ChatHistoryPanel, ChatMessageBubble,
│                               #   CitationBadge, ChatComposer
│
├── pages/                     # One component per route, wires a hook to UI.
│   ├── LoginPage.tsx
│   ├── DashboardPage.tsx
│   ├── ChatPage.tsx           # ⭐ RAG Knowledge Hub screen
│   ├── TranslationPage.tsx
│   └── FlashcardPage.tsx
│
├── router/
│   └── AppRouter.tsx          # Route table + auth guard
│
├── App.tsx                    # Providers + <BrowserRouter>
└── main.tsx
```

## Swapping mocks for the real FastAPI backend

Every function in `services/*.ts` has the same signature it will have once
it calls the real API — only the body changes. Example for `chatService.sendMessage`:

```ts
// before (mock)
await delay(1800);
// ...builds a fake ChatMessage from mock/mockData.ts

// after (real)
const res = await fetch(`${API_BASE}/chat/messages`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload),
});
return res.json(); // must resolve to ApiResult<SendMessageResponse>
```

No hook, component, or page needs to change — they only depend on the
types in `src/types/index.ts`.

## RAG chat contract

`ChatMessage` carries both `original_answer` (raw LLM output, kept for
debugging/eval purposes) and `content` (the rendered markdown shown to the
user), plus a `citations[]` array of `{ sourceTitle, pageOrSection }`. The
composer shows a pending bubble with a typing indicator (`status: "pending"`)
until the backend resolves.
