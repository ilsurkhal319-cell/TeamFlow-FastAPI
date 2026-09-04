import { FormEvent, useState } from 'react';
import { Archive, Star, Trash2, UsersRound } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import { api } from '../api';
import type { BoardSummary, User, Workspace } from '../types';
import NotificationsMenu from '../components/NotificationsMenu';
import JoinBoardModal from '../components/JoinBoardModal';
import UserMenu from '../components/UserMenu';

type Props = { user: User | null; workspaces: Workspace[]; boards: BoardSummary[]; activeWorkspaceId?: number; onSelect: (board: BoardSummary) => void; onRefresh: () => void; onWorkspace: (workspace: Workspace) => void };

export default function DashboardPage({ user, workspaces, boards, activeWorkspaceId, onSelect, onRefresh, onWorkspace }: Props) {
  const path = window.location.pathname;
  const active = path.startsWith('/favorites') ? '/favorites/' : path.startsWith('/archive') ? '/archive/' : path.startsWith('/profile') ? '/profile/' : '/dashboard/';
  const baseVisible = active === '/favorites/' ? boards.filter((item) => item.is_favorite) : active === '/archive/' ? boards.filter((item) => item.is_archived) : boards;
  const [search, setSearch] = useState('');
  const visible = baseVisible.filter((item) => !search.trim() || `${item.title} ${item.description || ''}`.toLowerCase().includes(search.trim().toLowerCase()));
  const [modal, setModal] = useState<'board' | 'workspace' | null>(() => new URLSearchParams(window.location.search).get('new') as 'board' | 'workspace' | null);
  const [joinOpen, setJoinOpen] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = new FormData(event.currentTarget);
    if (modal === 'workspace') await api('/workspaces', { method: 'POST', body: JSON.stringify({ name: values.get('name'), description: values.get('description') || '' }) });
    if (modal === 'board') {
      const targetWorkspace = workspaces.find((item) => item.id === activeWorkspaceId) || workspaces[0];
      if (!targetWorkspace) throw new Error('Сначала создайте рабочее пространство');
      await api(`/workspaces/${targetWorkspace.id}/boards`, { method: 'POST', body: JSON.stringify({ title: values.get('title'), description: values.get('description') || '', color: '#8b5cf6' }) });
    }
    setModal(null); window.history.replaceState({}, '', '/dashboard/'); onRefresh();
  }

  async function toggleBoardAction(boardId: number, action: 'favorite' | 'archive') {
    try {
      const target = boards.find((item) => item.id === boardId);
      if (!target?.workspace_id) return;
      await api(`/workspaces/${target.workspace_id}/boards/${boardId}/${action}`, { method: 'POST' });
      onRefresh();
    } catch (error) { window.alert(error instanceof Error ? error.message : 'Не удалось обновить доску'); }
  }

  async function deleteBoard(board: BoardSummary) {
    if (!window.confirm(`Удалить доску «${board.title}»? Все задачи и колонки будут удалены.`)) return;
    try {
      if (!board.workspace_id) return;
      await api(`/workspaces/${board.workspace_id}/boards/${board.id}`, { method: 'DELETE' });
      onRefresh();
    } catch (error) { window.alert(error instanceof Error ? error.message : 'Не удалось удалить доску'); }
  }

  return <div className="min-h-screen bg-zinc-950 text-zinc-100">
    <header className="fixed left-0 right-0 top-0 z-50 flex h-16 items-center justify-between border-b border-zinc-800 bg-zinc-950 px-6"><a href="/dashboard/" className="flex items-center gap-2"><span className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-600 text-lg font-bold">T</span><span className="text-xl font-semibold">TeamFlow</span></a><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Поиск по доскам..." className="hidden max-w-md flex-1 rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-2.5 text-sm placeholder-zinc-500 focus:border-violet-600 focus:outline-none lg:block"/><div className="flex items-center gap-3"><button onClick={() => setJoinOpen(true)} className="hidden rounded-xl border border-zinc-700 px-4 py-2.5 text-sm font-semibold text-zinc-300 hover:bg-zinc-800 sm:block">Ввести код</button><button onClick={() => setModal('board')} className="rounded-xl bg-violet-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-violet-700">+ Новая доска</button><NotificationsMenu /><UserMenu user={user}/></div></header>
    <Sidebar user={user} workspaces={workspaces} boards={boards} active={active} activeWorkspaceId={activeWorkspaceId} onWorkspace={onWorkspace} onCreateWorkspace={() => setModal('workspace')} onCreateBoard={() => setModal('board')} />
    <main className="mx-auto max-w-7xl px-6 pb-16 pt-28 lg:ml-[280px]"><div className="mb-8"><h1 className="mb-2 text-3xl font-bold">{active === '/favorites/' ? 'Избранное' : active === '/archive/' ? 'Архив' : active === '/profile/' ? 'Профиль' : `Добро пожаловать, ${user?.name || ''}! 👋`}</h1><p className="text-zinc-400">{active === '/dashboard/' ? 'Вот над чем ты работаешь сегодня' : 'Твои доски TeamFlow'}</p></div><div className="mb-10 grid gap-4 md:grid-cols-3"><button onClick={() => setModal('board')} className="flex items-center gap-4 rounded-2xl bg-zinc-900 p-5 text-left transition-all hover:bg-zinc-800 hover:shadow-xl"><span className="flex h-12 w-12 items-center justify-center rounded-xl bg-violet-600/20 text-2xl text-violet-400">+</span><span><strong className="block font-semibold">Создать новую доску</strong><small className="text-sm text-zinc-400">Начни новый проект</small></span></button><button onClick={() => setJoinOpen(true)} className="flex items-center gap-4 rounded-2xl bg-zinc-900 p-5 text-left transition-all hover:bg-zinc-800 hover:shadow-xl"><span className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600/20 text-xl text-blue-400">♟</span><span><strong className="block font-semibold">Присоединиться к доске</strong><small className="text-sm text-zinc-400">Введи код приглашения</small></span></button><button onClick={() => setModal('workspace')} className="flex items-center gap-4 rounded-2xl bg-zinc-900 p-5 text-left hover:bg-zinc-800"><span className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-600/20 text-xl text-emerald-400">+</span><span><strong className="block font-semibold">Новое пространство</strong><small className="text-sm text-zinc-400">Организуй команду</small></span></button></div><div className="mb-4 flex items-center justify-between"><h2 className="text-2xl font-semibold">{active === '/dashboard/' ? 'Мои доски' : active === '/favorites/' ? 'Избранные доски' : 'Архивные доски'}</h2><span className="text-sm text-zinc-500">{visible.length} доски</span></div><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{visible.map((item) => { const shared = item.is_shared ?? (activeWorkspaceId !== undefined && item.workspace_id !== undefined && item.workspace_id !== activeWorkspaceId); return <div key={item.id} onClick={() => onSelect(item)} onKeyDown={(event) => { if (event.key === 'Enter') onSelect(item); }} role="button" tabIndex={0} className="group relative cursor-pointer rounded-2xl border border-zinc-800 bg-zinc-900 p-5 text-left transition-all hover:-translate-y-1 hover:border-violet-600 hover:shadow-xl"><div className="mb-5 flex items-center justify-between"><span className="h-3 w-3 rounded-full" style={{ background: item.color }}/>{shared && <span className="inline-flex items-center gap-1 rounded-full border border-sky-400/20 bg-sky-400/10 px-2 py-1 text-[10px] font-medium text-sky-300"><UsersRound className="h-3 w-3"/>Общая доска</span>}</div><h3 className="mb-2 text-lg font-semibold">{item.title}</h3><p className="line-clamp-2 text-sm text-zinc-400">{item.description || 'Рабочая доска TeamFlow'}</p><div className="mt-5 flex justify-between border-t border-zinc-800 pt-4 text-xs text-zinc-500"><span>Открыть доску →</span><span>{item.is_archived ? 'Архив' : 'Активна'}</span></div>{!shared && <div className="absolute right-3 top-3 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100"><button onClick={(event) => { event.stopPropagation(); toggleBoardAction(item.id, 'favorite'); }} className={`rounded-lg p-2 hover:bg-zinc-800 ${item.is_favorite ? 'text-amber-400' : 'text-zinc-400'}`} title={item.is_favorite ? 'Убрать из избранного' : 'В избранное'}><Star className="h-4 w-4" fill={item.is_favorite ? 'currentColor' : 'none'} /></button><button onClick={(event) => { event.stopPropagation(); toggleBoardAction(item.id, 'archive'); }} className="rounded-lg p-2 text-zinc-400 hover:bg-zinc-800" title={item.is_archived ? 'Вернуть из архива' : 'В архив'}><Archive className="h-4 w-4" /></button><button onClick={(event) => { event.stopPropagation(); deleteBoard(item); }} className="rounded-lg p-2 text-zinc-400 hover:bg-red-500/20 hover:text-red-400" title="Удалить доску"><Trash2 className="h-4 w-4" /></button></div>}</div>; })}</div></main>
    {modal && <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 p-4"><form onSubmit={submit} className="w-full max-w-md rounded-3xl border border-zinc-800 bg-zinc-900 p-6 shadow-2xl"><h2 className="mb-5 text-xl font-semibold">{modal === 'board' ? 'Новая доска' : 'Новое рабочее пространство'}</h2><label className="mb-4 block text-sm text-zinc-300">Название<input name={modal === 'board' ? 'title' : 'name'} required autoFocus className="mt-2 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-4 py-3 focus:border-violet-600 focus:outline-none"/></label><label className="mb-5 block text-sm text-zinc-300">Описание<textarea name="description" rows={3} className="mt-2 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-4 py-3 focus:border-violet-600 focus:outline-none"/></label><div className="flex gap-3"><button type="button" onClick={() => setModal(null)} className="flex-1 rounded-xl border border-zinc-700 px-4 py-3 text-zinc-300">Отмена</button><button className="flex-1 rounded-xl bg-violet-600 px-4 py-3 font-semibold text-white">Создать</button></div></form></div>}
    <JoinBoardModal open={joinOpen} onClose={() => setJoinOpen(false)} />
  </div>;
}
