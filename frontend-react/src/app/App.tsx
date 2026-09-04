import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import { Check, MessageCircle, Pencil, Trash2, X } from 'lucide-react';
import { api, ApiError } from '../api';
import AuthPage from '../pages/AuthPage';
import DashboardPage from '../pages/DashboardPage';
import LandingPage from '../pages/LandingPage';
import ProfilePage from '../pages/ProfilePage';
import NotificationsMenu from '../components/NotificationsMenu';
import TeamModal from '../components/TeamModal';
import TaskDetailsModal from '../components/TaskDetailsModal';
import UserMenu from '../components/UserMenu';
import { useBoardRealtime } from '../hooks/useBoardRealtime';
import Avatar from '../components/Avatar';
import type { Board, Task, User, Workspace } from '../types';

const priorityLabels = { low: 'Низкий', medium: 'Средний', high: 'Высокий' };
const columnLabels: Record<string, string> = { backlog: 'Запланировано', 'in progress': 'В работе', review: 'На проверке', done: 'Готово' };

function displayColumnTitle(title: string) { return columnLabels[title.trim().toLowerCase()] || title; }


function App() {
  const [user, setUser] = useState<User | null>(null);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [board, setBoard] = useState<Board | null>(null);
  const [boards, setBoards] = useState<Board[]>([]);
  const [query, setQuery] = useState('');
  const [modal, setModal] = useState(false);
  const [columnId, setColumnId] = useState<number | null>(null);
  const [priority, setPriority] = useState<'low' | 'medium' | 'high'>('medium');
  const [collapsed, setCollapsed] = useState<number[]>([]);
  const [dragged, setDragged] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [teamOpen, setTeamOpen] = useState(false);
  const [editingTitle, setEditingTitle] = useState(false);
  const [titleDraft, setTitleDraft] = useState('');
  const [savingTitle, setSavingTitle] = useState(false);
  const [taskDetails, setTaskDetails] = useState<Task | null>(null);

  useEffect(() => { (async () => {
    try {
      if (window.location.pathname === '/' || window.location.pathname.startsWith('/login') || window.location.pathname.startsWith('/register')) {
        const token = localStorage.getItem('teamflow_token');
        if (window.location.pathname === '/' && !token) { setLoading(false); return; }
        if (window.location.pathname.startsWith('/login') || window.location.pathname.startsWith('/register')) { setLoading(false); return; }
      }
      const token = localStorage.getItem('teamflow_token');
      if (!token) { window.location.replace('/login/'); return; }
      else setUser(await api<User>('/auth/me'));
      const spaces = await api<Workspace[]>('/workspaces'); setWorkspaces(spaces); const savedWorkspaceId = Number(localStorage.getItem('teamflow_active_workspace')); const current = spaces.find((space) => space.id === savedWorkspaceId) || spaces[0]; setWorkspace(current); if (current) localStorage.setItem('teamflow_active_workspace', String(current.id));
      const archivedQuery = window.location.pathname.startsWith('/archive/') ? '?archived=true' : ''; const list = await api<Board[]>(`/boards${archivedQuery}`); setBoards(list); const routeId = Number(window.location.pathname.match(/board\/(\d+)/)?.[1]); const selected = list.find((item) => item.id === routeId) || (window.location.pathname.includes('/board/') ? undefined : list[0]); if (selected) setBoard(await api<Board>(`/workspaces/${selected.workspace_id || current?.id}/boards/${selected.id}`));
    } catch (caught) { if (caught instanceof ApiError && caught.status === 401) { localStorage.removeItem('teamflow_token'); window.location.replace('/login/'); return; } setError(caught instanceof Error ? caught.message : 'Не удалось подключиться к API'); } finally { setLoading(false); }
  })(); }, []);

  const visibleColumns = useMemo(() => (board?.columns || []).map((column) => ({ ...column, tasks: column.tasks.filter((task) => !query || `${task.title} ${task.description || ''}`.toLowerCase().includes(query.toLowerCase())) })), [board, query]);

  async function selectBoard(next: { id: number; workspace_id?: number }) { const workspaceId = next.workspace_id || workspace?.id; if (!workspaceId) return; setBoard(await api<Board>(`/workspaces/${workspaceId}/boards/${next.id}`)); window.history.replaceState({}, '', `/board/${next.id}/`); }
  const refreshCurrentBoard = useCallback(() => {
    if (!board?.id || !board.workspace_id) return;
    api<Board>(`/workspaces/${board.workspace_id}/boards/${board.id}`).then(setBoard).catch(() => undefined);
  }, [board?.id, board?.workspace_id]);
  useBoardRealtime(board?.id, refreshCurrentBoard);
  function startTitleEdit() { if (!board?.can_edit) return; setTitleDraft(board.title); setEditingTitle(true); }
  function cancelTitleEdit() { if (savingTitle) return; setEditingTitle(false); setTitleDraft(''); }
  async function saveTitle(event: FormEvent<HTMLFormElement>) { event.preventDefault(); if (!board || !board.workspace_id || !board.can_edit) return; const title = titleDraft.trim(); if (!title) return; if (title === board.title) { cancelTitleEdit(); return; } setSavingTitle(true); try { const updated = await api<Board>(`/workspaces/${board.workspace_id}/boards/${board.id}`, { method: 'PATCH', body: JSON.stringify({ title }) }); setBoard(updated); setBoards((items) => items.map((item) => item.id === updated.id ? { ...item, title: updated.title } : item)); setEditingTitle(false); setTitleDraft(''); } catch (error) { window.alert(error instanceof Error ? error.message : 'Не удалось переименовать доску'); } finally { setSavingTitle(false); } }
  async function deleteTask(taskId: number) { try { await api(`/tasks/${taskId}`, { method: 'DELETE' }); setBoard((current) => current ? { ...current, columns: current.columns.map((column) => ({ ...column, tasks: column.tasks.filter((task) => task.id !== taskId) })) } : current); } catch (error) { window.alert(error instanceof Error ? error.message : 'Не удалось удалить задачу'); } }
  async function refreshBoards() { const archivedQuery = window.location.pathname.startsWith('/archive/') ? '?archived=true' : ''; setBoards(await api<Board[]>(`/boards${archivedQuery}`)); }
  async function switchWorkspace(next: Workspace) { setWorkspace(next); localStorage.setItem('teamflow_active_workspace', String(next.id)); const archivedQuery = window.location.pathname.startsWith('/archive/') ? '?archived=true' : ''; const list = await api<Board[]>(`/boards${archivedQuery}`); setBoards(list); const selected = list.find((item) => item.workspace_id === next.id) || list[0]; if (selected) setBoard(await api<Board>(`/workspaces/${selected.workspace_id || next.id}/boards/${selected.id}`)); }
  async function moveTask(taskId: number, nextColumnId: number) { if (!board || !dragged) return; const previous = board; const task = board.columns.flatMap((item) => item.tasks).find((item) => item.id === taskId); if (!task) return; setBoard({ ...board, columns: board.columns.map((column) => ({ ...column, tasks: column.id === nextColumnId ? [...column.tasks, task] : column.tasks.filter((item) => item.id !== taskId) })) }); try { await api(`/tasks/${taskId}`, { method: 'PATCH', body: JSON.stringify({ column_id: nextColumnId }) }); } catch { setBoard(previous); } setDragged(null); }
  async function createTask(event: FormEvent<HTMLFormElement>) { event.preventDefault(); if (!board || columnId === null) return; const values = new FormData(event.currentTarget); const task = await api<Task>('/tasks', { method: 'POST', body: JSON.stringify({ column_id: columnId, title: values.get('title'), description: values.get('description') || '', priority }) }); setBoard({ ...board, columns: board.columns.map((column) => column.id === columnId ? { ...column, tasks: [...column.tasks, task] } : column) }); setModal(false); event.currentTarget.reset(); setPriority('medium'); }

  const path = window.location.pathname;
  async function tryDemo() {
    try {
      const session = await api<{ access_token: string }>('/auth/demo', { method: 'POST' });
      localStorage.setItem('teamflow_token', session.access_token);
      window.location.href = '/dashboard/';
    } catch (caught) {
      window.alert(caught instanceof Error ? caught.message : 'Демо-режим недоступен');
    }
  }
  if (path === '/') return <LandingPage user={user} boards={boards} board={board} loading={loading} onTryDemo={tryDemo} />;
  if (path.startsWith('/login')) return <AuthPage mode="login" onAuthenticated={() => { window.location.href = '/dashboard/'; }} />;
  if (path.startsWith('/register')) return <AuthPage mode="register" onAuthenticated={() => { window.location.href = '/dashboard/'; }} />;
  if (loading) return <div className="flex min-h-screen items-center justify-center bg-zinc-950 text-zinc-400">Загрузка TeamFlow…</div>;
  if (error && !user) return <div className="flex min-h-screen items-center justify-center bg-zinc-950"><div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-8 text-center"><h1 className="mb-2 text-xl font-semibold">Не удалось загрузить TeamFlow</h1><p className="mb-5 text-sm text-zinc-400">{error}</p><button onClick={() => { localStorage.removeItem('teamflow_token'); window.location.href = '/login/'; }} className="rounded-xl bg-violet-600 px-5 py-2.5 text-sm font-semibold">Войти заново</button></div></div>;
  if (path.startsWith('/profile') && user) return <ProfilePage user={user} workspaces={workspaces} boards={boards} activeWorkspaceId={workspace?.id} onSelect={selectBoard} onRefresh={refreshBoards} onWorkspace={switchWorkspace} onCreateWorkspace={() => window.location.href = '/dashboard/?new=workspace'} onCreateBoard={() => window.location.href = '/dashboard/?new=board'} />;
  if (!board) return <DashboardPage user={user} workspaces={workspaces} boards={boards} activeWorkspaceId={workspace?.id} onSelect={selectBoard} onRefresh={refreshBoards} onWorkspace={switchWorkspace} />;
  if (!window.location.pathname.includes('/board/')) return <DashboardPage user={user} workspaces={workspaces} boards={boards} activeWorkspaceId={workspace?.id} onSelect={selectBoard} onRefresh={refreshBoards} onWorkspace={switchWorkspace} />;

  return <div className="min-h-screen bg-zinc-950 text-zinc-100">
    <header className="fixed left-0 right-0 z-50 flex h-[60px] items-center justify-between border-b border-zinc-800 bg-zinc-950 px-6"><div className="flex min-w-0 items-center gap-4"><a href="/dashboard/" className="flex shrink-0 items-center gap-2 text-zinc-400 transition-colors hover:text-zinc-100"><span className="text-xl">‹</span><span className="text-sm">Все доски</span></a>{editingTitle ? <form onSubmit={saveTitle} className="flex min-w-0 items-center gap-1.5"><input value={titleDraft} onChange={(event) => setTitleDraft(event.target.value)} onKeyDown={(event) => { if (event.key === 'Escape') { event.preventDefault(); cancelTitleEdit(); } }} autoFocus maxLength={150} className="w-48 rounded-lg border border-violet-500 bg-zinc-900 px-3 py-1.5 text-base font-semibold text-zinc-100 outline-none focus:ring-2 focus:ring-violet-500/30 sm:w-64" aria-label="Название доски"/><button type="submit" disabled={savingTitle || !titleDraft.trim()} className="rounded-lg p-1.5 text-emerald-400 hover:bg-emerald-500/10 disabled:opacity-40" title="Сохранить"><Check className="h-4 w-4"/></button><button type="button" onClick={cancelTitleEdit} disabled={savingTitle} className="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-800 disabled:opacity-40" title="Отмена"><X className="h-4 w-4"/></button></form> : <div className="group flex min-w-0 items-center gap-2"><h1 className="truncate text-xl font-semibold">{board.title}</h1>{board.can_edit && <button onClick={startTitleEdit} className="rounded-md p-1 text-zinc-500 opacity-0 transition-opacity hover:bg-zinc-800 hover:text-zinc-200 group-hover:opacity-100 focus:opacity-100" title="Переименовать доску"><Pencil className="h-3.5 w-3.5"/></button>}</div>}{board.is_shared && <span className="hidden shrink-0 items-center rounded-full border border-sky-400/20 bg-sky-400/10 px-2.5 py-1 text-xs font-medium text-sky-300 sm:inline-flex">Общая доска</span>}</div><div className="mx-8 hidden max-w-xs flex-1 sm:block"><div className="relative"><input value={query} onChange={(event) => setQuery(event.target.value)} type="search" placeholder="Поиск по задачам..." className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-4 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-violet-600 focus:outline-none"/><span className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500">⌕</span></div></div><div className="flex items-center gap-3"><button onClick={() => setTeamOpen(true)} title="Управление командой доски" className="hidden items-center gap-2 rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-700 md:flex">Команда</button><NotificationsMenu /><UserMenu user={user} /></div></header>
    <main className="h-screen overflow-hidden px-6 pb-6 pt-[70px]"><div className="flex min-h-[calc(100vh-80px)] gap-6 overflow-x-auto overflow-y-auto scroll-smooth pb-20">{visibleColumns.map((column) => <div key={column.id} className="column flex min-w-[280px] flex-1 flex-col transition-all duration-300" data-column={column.id}><div className="rounded-t-3xl border-b border-zinc-800 bg-zinc-900 p-4"><div className="flex items-center justify-between"><div className="flex items-center gap-2"><button onClick={() => setCollapsed((items) => items.includes(column.id) ? items.filter((id) => id !== column.id) : [...items, column.id])} className="text-zinc-500 hover:text-zinc-300" title="Свернуть/развернуть">{collapsed.includes(column.id) ? '＋' : '−'}</button><h2 className="font-semibold text-zinc-100">{displayColumnTitle(column.title)}</h2><span className="rounded-full bg-zinc-800 px-2 py-0.5 text-xs text-zinc-400">{column.tasks.length}</span></div></div></div>{!collapsed.includes(column.id) && <div onDragOver={(event) => event.preventDefault()} onDrop={() => dragged && moveTask(dragged, column.id)} className="drop-zone flex-1 space-y-3 rounded-b-3xl bg-zinc-900/50 p-3" data-column-id={column.id}>{column.tasks.map((task) => <div key={task.id} draggable onDragStart={() => setDragged(task.id)} className="task-card cursor-grab rounded-3xl bg-zinc-900 p-5 shadow-xl transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl" data-task-id={task.id}><div className="mb-3 flex items-start justify-between"><span className="rounded-2xl bg-violet-500/10 px-2 py-1 text-xs font-medium text-violet-400">{priorityLabels[task.priority]}</span><div className="flex items-center gap-1"><button onClick={() => setTaskDetails(task)} className="rounded-lg p-1.5 text-zinc-500 hover:bg-violet-500/10 hover:text-violet-300" title="Комментарии"><MessageCircle className="h-4 w-4"/></button><button onClick={() => { if (window.confirm(`Удалить задачу «${task.title}»?`)) deleteTask(task.id); }} className="rounded-lg p-1.5 text-zinc-500 hover:bg-red-500/10 hover:text-red-400" title="Удалить задачу"><Trash2 className="h-4 w-4"/></button></div></div><h3 className="mb-2 text-base font-semibold">{task.title}</h3>{task.description && <p className="mb-3 line-clamp-2 text-sm text-zinc-400">{task.description}</p>}<div className="flex items-center justify-between border-t border-zinc-800 pt-3"><Avatar user={task.assignee}/>{task.due_date && <div className="flex items-center gap-1 text-sm text-zinc-400">◷ <span>{new Date(task.due_date).toLocaleDateString('ru-RU', { day: '2-digit', month: 'short' })}</span></div>}</div></div>)}<button onClick={() => { setColumnId(column.id); setPriority('medium'); setModal(true); }} className="w-full rounded-2xl border-2 border-dashed border-zinc-700 py-3 text-sm font-medium text-zinc-400 transition-colors hover:border-violet-600 hover:text-violet-400">+ Добавить задачу</button></div>}</div>)}</div></main>
    {modal && <div className="fixed inset-0 z-[100]" role="dialog" aria-modal="true"><div onClick={() => setModal(false)} className="absolute inset-0 bg-black/60 backdrop-blur-sm"/><form onSubmit={createTask} className="animate-modal-in absolute left-1/2 top-1/2 w-full max-w-md -translate-x-1/2 -translate-y-1/2 overflow-hidden rounded-3xl border border-zinc-800 bg-zinc-900 shadow-2xl"><div className="flex items-center justify-between border-b border-zinc-800 px-6 py-4"><h2 className="text-lg font-semibold">Новая задача</h2><button type="button" onClick={() => setModal(false)} className="p-1 text-zinc-400 hover:text-zinc-100">×</button></div><div className="space-y-4 p-6"><label className="block text-sm font-medium text-zinc-300">Название<input name="title" required autoFocus placeholder="Введите название задачи..." className="mt-2 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-4 py-3 text-zinc-100 placeholder-zinc-500 focus:border-violet-600 focus:outline-none"/></label><label className="block text-sm font-medium text-zinc-300">Описание <span className="text-zinc-500">(опционально)</span><textarea name="description" rows={3} placeholder="Добавьте описание задачи..." className="mt-2 w-full resize-none rounded-xl border border-zinc-700 bg-zinc-950 px-4 py-3 text-zinc-100 placeholder-zinc-500 focus:border-violet-600 focus:outline-none"/></label><div><span className="block text-sm font-medium text-zinc-300">Приоритет</span><div className="mt-2 flex gap-2">{(['low', 'medium', 'high'] as const).map((item) => <button key={item} type="button" onClick={() => setPriority(item)} className={`priority-btn flex-1 rounded-xl border px-3 py-2 text-sm font-medium transition-colors ${priority === item ? 'selected border-violet-600 text-violet-400' : 'border-zinc-700 text-zinc-400 hover:border-zinc-600'}`}>{priorityLabels[item]}</button>)}</div></div></div><div className="flex gap-3 border-t border-zinc-800 px-6 py-4"><button type="button" onClick={() => setModal(false)} className="flex-1 rounded-xl border border-zinc-700 px-4 py-3 font-medium text-zinc-300 hover:bg-zinc-800">Отмена</button><button className="flex-1 rounded-xl bg-violet-600 px-4 py-3 font-medium text-white hover:bg-violet-700">Создать</button></div></form></div>}
    <TeamModal boardId={board.id} open={teamOpen} onClose={() => setTeamOpen(false)} />
    <TaskDetailsModal task={taskDetails} open={taskDetails !== null} onClose={() => setTaskDetails(null)} onDeleted={deleteTask} />
  </div>;
}

export default App;
