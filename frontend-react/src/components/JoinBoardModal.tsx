import { FormEvent, useState } from 'react';
import { api, ApiError } from '../api';

type Props = { open: boolean; onClose: () => void };

export default function JoinBoardModal({ open, onClose }: Props) {
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setLoading(true);
    try {
      const result = await api<{ board_id: number }>('/invitations/claim', { method: 'POST', body: JSON.stringify({ code: code.trim() }) });
      window.location.href = `/board/${result.board_id}/`;
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Не удалось присоединиться к доске');
    } finally { setLoading(false); }
  }

  if (!open) return null;
  return <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/60 p-4" role="dialog" aria-modal="true" aria-label="Ввести код приглашения"><button className="absolute inset-0 cursor-default" onClick={onClose} aria-label="Закрыть" /><form onSubmit={submit} className="relative w-full max-w-md rounded-3xl border border-zinc-800 bg-zinc-900 p-6 shadow-2xl"><div className="mb-5 flex items-center justify-between"><h2 className="text-xl font-semibold">Присоединиться к доске</h2><button type="button" onClick={onClose} className="text-2xl text-zinc-400 hover:text-zinc-100" aria-label="Закрыть">×</button></div><p className="mb-4 text-sm text-zinc-400">Введи короткий код, который отправил владелец доски.</p><input autoFocus required minLength={4} maxLength={12} value={code} onChange={(event) => setCode(event.target.value.toUpperCase())} placeholder="Например, 7F3K9Q2A" className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-4 py-3 text-center text-lg font-semibold tracking-[0.2em] text-zinc-100 placeholder:text-sm placeholder:tracking-normal focus:border-violet-600 focus:outline-none" />{error && <p className="mt-3 text-sm text-red-400">{error}</p>}<div className="mt-6 flex gap-3"><button type="button" onClick={onClose} className="flex-1 rounded-xl border border-zinc-700 px-4 py-3 text-sm text-zinc-300 hover:bg-zinc-800">Отмена</button><button disabled={loading} className="flex-1 rounded-xl bg-violet-600 px-4 py-3 text-sm font-semibold text-white hover:bg-violet-700 disabled:opacity-50">{loading ? 'Подключение…' : 'Присоединиться'}</button></div></form></div>;
}
