import { User } from '../types';

export default function Avatar({ user, large = false }: { user?: User | null; large?: boolean }) {
  const initials = user?.name?.split(' ').map((part) => part[0]).join('').slice(0, 2).toUpperCase() || '—';
  return <span role="img" aria-label={`Аватар ${user?.name || ''}`} className={`flex ${large ? 'h-20 w-20 text-2xl' : 'h-7 w-7 text-xs'} items-center justify-center rounded-full bg-violet-600 font-semibold text-white`}>{initials}</span>;
}
