import { useEffect, useRef, useState } from 'react';
import { ChevronDown, LogOut, Settings, UserRound } from 'lucide-react';
import Avatar from './Avatar';
import { User } from '../types';

type Props = { user: User | null; fullWidth?: boolean; placement?: 'up' | 'down' };

export default function UserMenu({ user, fullWidth = false, placement = 'down' }: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const close = (event: MouseEvent) => { if (ref.current && !ref.current.contains(event.target as Node)) setOpen(false); };
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, []);

  function logout() {
    localStorage.removeItem('teamflow_token');
    window.location.replace('/login/');
  }

  return <div ref={ref} className={`relative ${fullWidth ? 'w-full' : ''}`}>
    <button onClick={() => setOpen((value) => !value)} className={`flex items-center gap-2 rounded-xl text-left text-sm text-zinc-300 transition-colors hover:bg-zinc-800 ${fullWidth ? 'w-full px-3 py-2.5' : 'px-2 py-1.5'}`} aria-expanded={open} aria-haspopup="menu"><Avatar user={user} /><span className={fullWidth ? 'min-w-0 flex-1 truncate' : 'hidden max-w-[150px] truncate sm:inline'}>{user?.name}</span><ChevronDown className={`h-4 w-4 shrink-0 text-zinc-500 transition-transform ${open ? 'rotate-180' : ''}`} /></button>
    {open && <div className={`absolute right-0 z-[130] w-52 overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900 p-1.5 shadow-2xl ${placement === 'up' ? 'bottom-full mb-2' : 'top-12'}`} role="menu">
      <a href="/profile/" className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-zinc-300 hover:bg-zinc-800" role="menuitem"><UserRound className="h-4 w-4 text-zinc-500" />Профиль</a>
      <a href="/profile/#settings" className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-zinc-300 hover:bg-zinc-800" role="menuitem"><Settings className="h-4 w-4 text-zinc-500" />Настройки</a>
      <div className="my-1 border-t border-zinc-800" />
      <button onClick={logout} className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-red-400 hover:bg-red-500/10" role="menuitem"><LogOut className="h-4 w-4" />Выйти</button>
    </div>}
  </div>;
}
