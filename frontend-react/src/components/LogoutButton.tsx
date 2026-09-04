import { LogOut } from 'lucide-react';

export default function LogoutButton({ compact = false }: { compact?: boolean }) {
  function logout() {
    localStorage.removeItem('teamflow_token');
    window.location.replace('/login/');
  }

  return <button onClick={logout} className={`flex items-center gap-2 rounded-xl text-sm text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-zinc-100 ${compact ? 'p-2' : 'w-full px-3 py-2.5'}`} title="Выйти из аккаунта"><LogOut className="h-4 w-4" />{!compact && 'Выйти'}</button>;
}
