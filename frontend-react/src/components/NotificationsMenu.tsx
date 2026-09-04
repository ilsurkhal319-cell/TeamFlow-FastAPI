import { useEffect, useRef, useState } from 'react';
import { Bell, Check, X } from 'lucide-react';
import { api, ApiError } from '../api';
import Avatar from './Avatar';
import { Notification } from '../types';

export default function NotificationsMenu() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<Notification[]>([]);
  const [unread, setUnread] = useState(0);
  const [busy, setBusy] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  async function load() {
    try {
      const [next, count] = await Promise.all([
        api<Notification[]>('/notifications'),
        api<{ unread_count: number }>('/notifications/unread-count'),
      ]);
      setItems(next);
      setUnread(count.unread_count);
    } catch {
      setItems([]);
    }
  }

  useEffect(() => {
    load();
    const close = (event: MouseEvent) => { if (ref.current && !ref.current.contains(event.target as Node)) setOpen(false); };
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, []);

  async function markAll() {
    await api('/notifications/read-all', { method: 'POST' });
    setItems((current) => current.map((item) => ({ ...item, is_read: true })));
    setUnread(0);
  }

  async function respond(item: Notification, action: 'accept' | 'decline') {
    if (!item.invitation_id) return;
    setBusy(true);
    try {
      await api(`/invitations/${item.invitation_id}/${action}`, { method: 'POST' });
      setItems((current) => current.filter((notification) => notification.id !== item.id));
      if (!item.is_read) setUnread((count) => Math.max(0, count - 1));
    } catch (error) {
      const message = error instanceof ApiError ? error.message : 'Не удалось обработать приглашение';
      window.alert(message);
    } finally { setBusy(false); }
  }

  return <div className="relative" ref={ref}>
    <button onClick={() => { setOpen((value) => !value); if (!open) load(); }} className="relative rounded-xl p-2 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-zinc-100" aria-label="Уведомления">
      <Bell className="h-5 w-5" />
      {unread > 0 && <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-violet-600 px-1 text-[10px] font-bold text-white">{unread > 9 ? '9+' : unread}</span>}
    </button>
    {open && <div className="absolute right-0 top-12 z-[120] w-[360px] overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900 shadow-2xl">
      <div className="flex items-center justify-between border-b border-zinc-800 px-4 py-3"><h2 className="font-semibold">Уведомления</h2>{unread > 0 && <button onClick={markAll} className="text-xs text-violet-400 hover:text-violet-300">Прочитать все</button>}</div>
      <div className="max-h-[420px] overflow-y-auto">
        {items.length === 0 && <p className="px-4 py-8 text-center text-sm text-zinc-500">Новых уведомлений нет</p>}
        {items.map((item) => <div key={item.id} className={`border-b border-zinc-800/80 px-4 py-3 ${item.is_read ? 'opacity-60' : ''}`}>
          <div className="flex gap-3"><Avatar user={item.actor} /><div className="min-w-0 flex-1"><div className="flex items-start justify-between gap-2"><p className="text-sm font-medium text-zinc-100">{item.title}</p>{!item.is_read && <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-violet-500" />}</div><p className="mt-1 text-xs leading-5 text-zinc-400">{item.message}</p><p className="mt-1 text-[11px] text-zinc-600">{new Date(item.created_at).toLocaleString('ru-RU')}</p>
          {item.kind === 'board_invitation' && item.invitation_id && <div className="mt-3 flex gap-2"><button disabled={busy} onClick={() => respond(item, 'accept')} className="flex items-center gap-1 rounded-lg bg-violet-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-violet-700 disabled:opacity-50"><Check className="h-3.5 w-3.5" />Принять</button><button disabled={busy} onClick={() => respond(item, 'decline')} className="flex items-center gap-1 rounded-lg border border-zinc-700 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-800 disabled:opacity-50"><X className="h-3.5 w-3.5" />Отклонить</button></div>}
          </div></div>
        </div>)}
      </div>
    </div>}
  </div>;
}
