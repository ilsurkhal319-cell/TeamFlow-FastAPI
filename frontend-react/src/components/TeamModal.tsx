import { FormEvent, useEffect, useState } from 'react';
import { BoardMember } from '../types';
import { api, ApiError } from '../api';
import Avatar from './Avatar';

type Props = { boardId: number; open: boolean; onClose: () => void };

export default function TeamModal({ boardId, open, onClose }: Props) {
  const [members, setMembers] = useState<BoardMember[]>([]);
  const [ownerId, setOwnerId] = useState<number | null>(null);
  const [inviteCode, setInviteCode] = useState('');
  const [username, setUsername] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
    setMessage(''); setError(''); setInviteCode(''); setUsername('');
    api<{ members: BoardMember[]; owner_id: number }>(`/boards/${boardId}/members`).then((data) => { setMembers(data.members); setOwnerId(data.owner_id); }).catch(() => setError('Не удалось загрузить участников'));
  }, [boardId, open]);

  async function invite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true); setError(''); setMessage('');
    try {
      const invitation = await api<{ code: string }>(`/boards/${boardId}/invitations`, { method: 'POST', body: JSON.stringify(username.trim() ? { username: username.trim() } : {}) });
      setInviteCode(invitation.code); setMessage(username.trim() ? 'Приглашение отправлено пользователю' : 'Код создан — отправьте его участнику');
      setUsername('');
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Не удалось отправить приглашение');
    } finally { setLoading(false); }
  }

  if (!open) return null;
  return <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/60 p-4" role="dialog" aria-modal="true" aria-label="Команда доски">
    <button className="absolute inset-0 cursor-default" onClick={onClose} aria-label="Закрыть" />
    <div className="relative w-full max-w-lg overflow-hidden rounded-3xl border border-zinc-800 bg-zinc-900 shadow-2xl">
      <div className="flex items-center justify-between border-b border-zinc-800 px-6 py-4"><div><h2 className="text-lg font-semibold">Команда доски</h2><p className="mt-1 text-xs text-zinc-500">Участники видят задачи и могут работать с ними</p></div><button onClick={onClose} className="text-2xl leading-none text-zinc-400 hover:text-zinc-100" aria-label="Закрыть">×</button></div>
      <div className="max-h-[360px] space-y-2 overflow-y-auto p-6">{members.map((member) => <div key={member.id} className="flex items-center gap-3 rounded-xl bg-zinc-950/60 px-3 py-2.5"><Avatar user={member} /><div className="min-w-0 flex-1"><p className="truncate text-sm font-medium">{member.name}</p><p className="truncate text-xs text-zinc-500">{member.email}</p></div>{member.id === ownerId && <span className="text-xs text-violet-400">Владелец</span>}</div>)}{members.length === 0 && <p className="text-sm text-zinc-500">В команде пока никого нет</p>}</div>
      <form onSubmit={invite} className="border-t border-zinc-800 p-6"><p className="text-sm text-zinc-400">Пригласите по уникальному username или создайте короткий код для передачи.</p><label className="mt-4 block text-sm font-medium text-zinc-300">Username участника <span className="text-zinc-500">(необязательно)</span><input value={username} onChange={(event) => setUsername(event.target.value.toLowerCase())} placeholder="например, alex" className="mt-2 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-4 py-3 text-zinc-100 placeholder-zinc-500 focus:border-violet-600 focus:outline-none" /></label>{inviteCode && <div className="mt-4 flex items-center gap-2 rounded-xl border border-violet-500/40 bg-violet-500/10 px-4 py-3"><code className="flex-1 text-lg font-bold tracking-[0.25em] text-violet-300">{inviteCode}</code><button type="button" onClick={() => navigator.clipboard?.writeText(inviteCode)} className="text-xs text-violet-300 hover:text-white">Копировать</button></div>}{message && <p className="mt-3 text-sm text-emerald-400">{message}</p>}{error && <p className="mt-3 text-sm text-red-400">{error}</p>}<div className="mt-5 flex gap-3"><button type="button" onClick={onClose} className="flex-1 rounded-xl border border-zinc-700 px-4 py-3 text-sm font-medium text-zinc-300 hover:bg-zinc-800">Закрыть</button><button disabled={loading} className="flex-1 rounded-xl bg-violet-600 px-4 py-3 text-sm font-semibold text-white hover:bg-violet-700 disabled:opacity-50">{loading ? 'Отправка…' : username ? 'Пригласить по username' : 'Создать код'}</button></div></form>
    </div>
  </div>;
}
