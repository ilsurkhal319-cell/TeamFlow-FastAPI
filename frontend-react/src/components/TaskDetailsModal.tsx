import { FormEvent, useEffect, useState } from 'react';
import { MessageCircle, Send, Trash2, X } from 'lucide-react';
import { api, ApiError } from '../api';
import Avatar from './Avatar';
import { Comment, Task } from '../types';

type Props = { task: Task | null; open: boolean; onClose: () => void; onDeleted: (taskId: number) => void };

export default function TaskDetailsModal({ task, open, onClose, onDeleted }: Props) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (!open || !task) return;
    setLoading(true);
    api<Comment[]>(`/tasks/${task.id}/comments`).then(setComments).catch(() => setComments([])).finally(() => setLoading(false));
  }, [open, task]);

  if (!open || !task) return null;
  const currentTask = task;

  async function addComment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = text.trim();
    if (!value || sending) return;
    setSending(true);
    try {
      const comment = await api<Comment>(`/tasks/${currentTask.id}/comments`, { method: 'POST', body: JSON.stringify({ text: value }) });
      setComments((current) => [...current, comment]);
      setText('');
    } catch (error) {
      window.alert(error instanceof ApiError ? error.message : 'Не удалось добавить комментарий');
    } finally { setSending(false); }
  }

  async function removeTask() {
    if (!window.confirm(`Удалить задачу «${currentTask.title}»?`)) return;
    try {
      await api(`/tasks/${currentTask.id}`, { method: 'DELETE' });
      onDeleted(currentTask.id);
      onClose();
    } catch (error) {
      window.alert(error instanceof ApiError ? error.message : 'Не удалось удалить задачу');
    }
  }

  return <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm" role="dialog" aria-modal="true" aria-label="Детали задачи">
    <div className="flex max-h-[min(720px,calc(100vh-2rem))] w-full max-w-2xl flex-col overflow-hidden rounded-3xl border border-zinc-800 bg-zinc-900 shadow-2xl">
      <div className="flex items-start justify-between border-b border-zinc-800 px-6 py-5"><div className="min-w-0 pr-4"><div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-violet-400"><MessageCircle className="h-4 w-4"/>Задача</div><h2 className="truncate text-xl font-semibold text-zinc-100">{task.title}</h2>{task.description && <p className="mt-2 text-sm leading-6 text-zinc-400">{task.description}</p>}</div><button onClick={onClose} className="rounded-lg p-2 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100" title="Закрыть"><X className="h-5 w-5"/></button></div>
      <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5"><div className="mb-5 flex items-center justify-between"><h3 className="text-sm font-semibold text-zinc-200">Комментарии</h3><span className="text-xs text-zinc-500">{comments.length}</span></div>{loading && <p className="py-8 text-center text-sm text-zinc-500">Загрузка комментариев…</p>}{!loading && comments.length === 0 && <p className="rounded-2xl border border-dashed border-zinc-700 px-4 py-8 text-center text-sm text-zinc-500">Пока нет комментариев. Будь первым.</p>}{!loading && comments.length > 0 && <div className="space-y-4">{comments.map((comment) => <div key={comment.id} className="flex gap-3"><Avatar user={comment.author}/><div className="min-w-0 flex-1 rounded-2xl bg-zinc-950/70 px-4 py-3"><div className="flex items-baseline justify-between gap-3"><strong className="truncate text-sm text-zinc-200">{comment.author.name}</strong><time className="shrink-0 text-[11px] text-zinc-600">{new Date(comment.created_at).toLocaleString('ru-RU')}</time></div><p className="mt-1 whitespace-pre-wrap text-sm leading-6 text-zinc-400">{comment.text}</p></div></div>)}</div>}</div>
      <form onSubmit={addComment} className="border-t border-zinc-800 p-5"><label className="sr-only" htmlFor="task-comment">Комментарий</label><div className="flex items-end gap-3"><textarea id="task-comment" value={text} onChange={(event) => setText(event.target.value)} rows={2} maxLength={2000} placeholder="Напишите комментарий…" className="min-h-[72px] flex-1 resize-none rounded-2xl border border-zinc-700 bg-zinc-950 px-4 py-3 text-sm text-zinc-100 outline-none placeholder:text-zinc-600 focus:border-violet-500"/><button type="submit" disabled={sending || !text.trim()} className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-violet-600 text-white transition-colors hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-40" title="Добавить комментарий"><Send className="h-4 w-4"/></button></div><button type="button" onClick={removeTask} className="mt-4 inline-flex items-center gap-2 text-xs text-red-400 hover:text-red-300"><Trash2 className="h-3.5 w-3.5"/>Удалить задачу</button></form>
    </div>
  </div>;
}
