import type { ReactNode } from 'react';
import {
  ArrowRight,
  Check,
  CheckSquare,
  LayoutDashboard,
  Palette,
  PlayCircle,
  ShieldCheck,
  Users,
  Zap,
} from 'lucide-react';

function DemoShell({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950 shadow-inner">
      <div className="flex h-8 items-center gap-1.5 border-b border-zinc-800 bg-zinc-900 px-3">
        <span className="h-2.5 w-2.5 rounded-full bg-red-400/80" />
        <span className="h-2.5 w-2.5 rounded-full bg-amber-400/80" />
        <span className="h-2.5 w-2.5 rounded-full bg-emerald-400/80" />
        <div className="ml-3 h-3 w-28 rounded-full bg-zinc-800" />
      </div>
      {children}
    </div>
  );
}

function WorkspacePreview() {
  return (
    <DemoShell>
      <div className="flex min-h-[190px] bg-zinc-950">
        <div className="hidden w-28 border-r border-zinc-800 bg-zinc-900/80 p-3 sm:block">
          <div className="mb-5 flex items-center gap-1.5"><span className="h-5 w-5 rounded-md bg-violet-500" /><span className="h-2 w-12 rounded bg-zinc-600" /></div>
          <div className="space-y-2"><span className="block h-2 w-16 rounded bg-violet-400/70" /><span className="block h-2 w-12 rounded bg-zinc-700" /><span className="block h-2 w-14 rounded bg-zinc-700" /></div>
        </div>
        <div className="flex-1 p-4">
          <div className="mb-4 flex items-center justify-between"><div><div className="mb-1 h-3 w-28 rounded bg-zinc-200/90" /><div className="h-2 w-20 rounded bg-zinc-700" /></div><span className="h-7 w-20 rounded-lg bg-violet-600" /></div>
          <div className="grid gap-2 sm:grid-cols-3"><div className="h-20 rounded-lg border border-zinc-800 bg-zinc-900 p-3"><span className="block h-2 w-10 rounded bg-zinc-600" /><span className="mt-3 block h-5 w-8 rounded bg-violet-400/50" /></div><div className="h-20 rounded-lg border border-zinc-800 bg-zinc-900 p-3"><span className="block h-2 w-12 rounded bg-zinc-600" /><span className="mt-3 block h-5 w-8 rounded bg-blue-400/50" /></div><div className="h-20 rounded-lg border border-zinc-800 bg-zinc-900 p-3"><span className="block h-2 w-14 rounded bg-zinc-600" /><span className="mt-3 block h-5 w-8 rounded bg-emerald-400/50" /></div></div>
        </div>
      </div>
    </DemoShell>
  );
}

function BoardPreview() {
  return (
    <DemoShell>
      <div className="min-h-[190px] bg-zinc-950 p-4">
        <div className="mb-4 flex items-center justify-between"><div className="h-3 w-32 rounded bg-zinc-200/90" /><span className="h-6 w-16 rounded-md bg-violet-600/80" /></div>
        <div className="grid grid-cols-3 gap-2"><div className="rounded-lg bg-zinc-900 p-2.5"><div className="mb-3 flex justify-between"><span className="h-2 w-12 rounded bg-zinc-500" /><span className="h-2 w-3 rounded bg-zinc-700" /></div><div className="space-y-2"><div className="h-9 rounded border border-zinc-800 bg-zinc-950 p-2"><span className="block h-2 w-14 rounded bg-zinc-600" /><span className="mt-1.5 block h-1.5 w-8 rounded bg-violet-400/70" /></div><div className="h-8 rounded border border-zinc-800 bg-zinc-950" /></div></div><div className="rounded-lg bg-zinc-900 p-2.5"><div className="mb-3 flex justify-between"><span className="h-2 w-16 rounded bg-zinc-500" /><span className="h-2 w-3 rounded bg-zinc-700" /></div><div className="h-10 rounded border border-zinc-800 bg-zinc-950 p-2"><span className="block h-2 w-12 rounded bg-zinc-600" /><span className="mt-2 block h-1.5 w-9 rounded bg-blue-400/70" /></div></div><div className="rounded-lg bg-zinc-900 p-2.5"><div className="mb-3 flex justify-between"><span className="h-2 w-10 rounded bg-zinc-500" /><span className="h-2 w-3 rounded bg-zinc-700" /></div><div className="h-9 rounded border border-zinc-800 bg-zinc-950 p-2"><span className="block h-2 w-14 rounded bg-zinc-600" /><span className="mt-1.5 block h-1.5 w-8 rounded bg-emerald-400/70" /></div></div></div>
      </div>
    </DemoShell>
  );
}

type LandingUser = { name: string };
type LandingBoard = { id: number; title: string; description?: string; color?: string; is_shared?: boolean; columns?: Array<{ tasks: unknown[] }> };

type LandingPageProps = {
  user?: LandingUser | null;
  boards?: LandingBoard[];
  board?: LandingBoard | null;
  loading?: boolean;
  onTryDemo?: () => void;
};

export default function LandingPage({ user, boards = [], board, loading = false, onTryDemo }: LandingPageProps) {
  const features = [
    [CheckSquare, 'Гибкие доски и колонки', 'Создавай любое количество досок. Перетаскивай задачи между колонками.', 'violet'],
    [Users, 'Командная работа', 'Приглашай участников и видите одну и ту же доску в реальном времени.', 'blue'],
    [CheckSquare, 'Мощная система задач', 'Приоритеты, быстрый drag-and-drop и комментарии.', 'emerald'],
    [Palette, 'Современный дизайн', 'Красивый тёмный интерфейс, полностью адаптивный.', 'pink'],
    [ShieldCheck, 'Безопасность', 'JWT авторизация и защита данных на уровне API.', 'amber'],
    [Zap, 'Быстрый и лёгкий', 'React-клиент и быстрый FastAPI backend.', 'cyan'],
  ] as const;

  const featuredBoard = boards[0] || board || null;
  const demoBoardHref = featuredBoard ? `/board/${featuredBoard.id}/` : '/dashboard/';
  const taskCount = board?.columns?.reduce((total, column) => total + column.tasks.length, 0);
  const displayName = user?.name || 'Alex Morgan';
  const firstName = displayName.split(' ')[0];
  const demos = [
    [LayoutDashboard, 'Рабочее пространство', 'Все доски и команда под рукой', WorkspacePreview, '/dashboard/'],
    [CheckSquare, 'Доска и задачи', 'Колонки, карточки, приоритеты и комментарии в одном месте', BoardPreview, demoBoardHref],
  ] as const;

  return (
    <div className="bg-zinc-950 text-zinc-100">
      <header className="fixed left-0 right-0 top-0 z-50 border-b border-zinc-800/50 bg-zinc-950/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <a href="/" className="flex items-center gap-2"><span className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-600 text-lg font-bold">T</span><span className="text-xl font-semibold">TeamFlow</span></a>
          <nav className="hidden items-center gap-8 md:flex"><a href="#features" className="text-zinc-400 hover:text-zinc-100">Функции</a><a href="#demo" className="text-zinc-400 hover:text-zinc-100">Примеры</a><a href="#why" className="text-zinc-400 hover:text-zinc-100">Почему мы</a></nav>
          <div className="flex items-center gap-3"><a href="/login/" className="hidden px-4 py-2 text-sm text-zinc-300 sm:block">Войти</a><a href="/register/" className="rounded-xl bg-violet-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-violet-700">Начать бесплатно</a></div>
        </div>
      </header>
      <section className="gradient-bg flex min-h-screen items-center justify-center pt-16">
        <div className="mx-auto grid max-w-7xl items-center gap-12 px-6 py-20 lg:grid-cols-2">
          <div className="text-center lg:text-left"><p className="mb-4 text-sm font-medium text-violet-300">{loading ? 'Загружаем рабочее пространство…' : user ? `Привет, ${firstName}!` : 'Командная работа без хаоса'}</p><h1 className="mb-6 text-4xl font-bold leading-tight md:text-5xl lg:text-6xl">Управляй задачами команды<br/><span className="text-violet-400">просто и красиво</span></h1><p className="mx-auto mb-8 max-w-xl text-lg text-zinc-400 lg:mx-0">Современная Kanban-доска на FastAPI и React. Создавай рабочие пространства, добавляй участников и работай в реальном времени.</p><div className="flex flex-col justify-center gap-4 sm:flex-row lg:justify-start"><a href="/register/" className="flex items-center justify-center gap-2 rounded-xl bg-violet-600 px-8 py-4 font-semibold text-white hover:bg-violet-700">Создать аккаунт бесплатно <ArrowRight className="h-5 w-5"/></a>{!user && <button onClick={onTryDemo} className="flex items-center justify-center gap-2 rounded-xl border border-violet-500/60 px-8 py-4 font-medium text-violet-200 hover:bg-violet-500/10"><PlayCircle className="h-5 w-5"/>Попробовать демо</button>}<a href="#demo" className="flex items-center justify-center gap-2 rounded-xl border border-zinc-700 px-8 py-4 font-medium text-zinc-300 hover:bg-zinc-900"><PlayCircle className="h-5 w-5"/>Посмотреть интерфейс</a></div></div>
          <div className="hidden lg:block"><a href="/dashboard/" className="block overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900 shadow-2xl hover:-translate-y-1"><div className="h-1.5 bg-violet-500"/><div className="p-6"><div className="mb-4 flex items-center justify-between"><span className="text-xs font-medium uppercase tracking-wider text-violet-300">{featuredBoard?.is_shared ? 'Общая доска' : 'Твоя доска'}</span><span className="rounded-full bg-violet-600/15 px-2 py-1 text-xs text-violet-300">{displayName.split(' ').map((part) => part[0]).join('').slice(0, 2).toUpperCase()}</span></div><h3 className="mb-2 text-lg font-semibold">{featuredBoard?.title || 'Создай первую доску'}</h3><p className="mb-4 line-clamp-1 text-sm text-zinc-400">{featuredBoard?.description || 'Управление задачами и командой'}</p><div className="mb-4 flex -space-x-2"><span className="flex h-7 w-7 items-center justify-center rounded-full border-2 border-zinc-900 bg-violet-600 text-xs font-semibold">{displayName.charAt(0).toUpperCase()}</span><span className="flex h-7 w-7 items-center justify-center rounded-full border-2 border-zinc-900 bg-blue-600 text-xs font-semibold">{featuredBoard ? 'T' : '+'}</span></div><div className="flex justify-between border-t border-zinc-800 pt-4 text-sm text-zinc-400"><span>{taskCount === undefined ? 'Открыть доску' : `${taskCount} задач`}</span><span>Открыть доски</span></div></div></a></div>
        </div>
      </section>
      <section id="features" className="bg-zinc-900/50 py-24"><div className="mx-auto max-w-7xl px-6"><h2 className="mb-16 text-center text-3xl font-bold md:text-4xl">Всё, что нужно для продуктивной работы</h2><div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">{features.map(([Icon, title, text, color]) => <div key={title} className="group rounded-3xl border border-zinc-800 bg-zinc-900 p-6 hover:border-violet-600/50"><div className={`mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-${color}-600/20`}><Icon className={`h-6 w-6 text-${color}-400`}/></div><h3 className="mb-2 text-xl font-semibold">{title}</h3><p className="text-zinc-400">{text}</p></div>)}</div></div></section>
      <section id="demo" className="py-24"><div className="mx-auto max-w-7xl px-6"><div className="mx-auto mb-12 max-w-2xl text-center"><p className="mb-3 text-sm font-semibold uppercase tracking-[0.24em] text-violet-400">Интерфейс</p><h2 className="mb-4 text-3xl font-bold md:text-4xl">Так выглядит TeamFlow</h2><p className="text-zinc-400">Продуманный интерфейс для досок, задач и командной работы — без лишней сложности.</p></div><div className="grid gap-6 md:grid-cols-2">{demos.map(([Icon, title, text, Preview, href]) => <a href={href} key={title} className="group overflow-hidden rounded-3xl border border-zinc-800 bg-zinc-900 hover:-translate-y-1 hover:border-violet-500/60"><div className="p-3"><Preview/></div><div className="flex items-start gap-3 border-t border-zinc-800 p-5"><span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-violet-600/15 text-violet-400"><Icon className="h-4 w-4"/></span><div className="min-w-0 flex-1"><h3 className="mb-1 font-semibold">{title}</h3><p className="text-sm text-zinc-400">{text}</p></div><ArrowRight className="mt-1 h-4 w-4 shrink-0 text-zinc-600"/></div></a>)}</div></div></section>
      <section id="why" className="bg-zinc-900/50 py-24"><div className="mx-auto max-w-4xl px-6 text-center"><h2 className="mb-8 text-3xl font-bold md:text-4xl">Почему выбирают TeamFlow</h2><div className="mx-auto grid max-w-2xl gap-3 text-left sm:grid-cols-2"><div className="flex items-center gap-2 text-zinc-300"><Check className="h-5 w-5 text-emerald-400"/>Понятная Kanban-логика</div><div className="flex items-center gap-2 text-zinc-300"><Check className="h-5 w-5 text-emerald-400"/>Безопасная авторизация</div><div className="flex items-center gap-2 text-zinc-300"><Check className="h-5 w-5 text-emerald-400"/>Уведомления команды</div><div className="flex items-center gap-2 text-zinc-300"><Check className="h-5 w-5 text-emerald-400"/>Адаптивный интерфейс</div></div></div></section>
    </div>
  );
}
