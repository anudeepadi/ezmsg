'use client';

import { useState, FormEvent } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { Header } from '@/components/layout';
import { templates, ApiError } from '@/lib/api';
import { useToastStore } from '@/lib/store';
import { ArrowLeft, Plus, Globe } from 'lucide-react';

const TEMPLATE_TYPES = ['STANDARD', 'SURVEY', 'NOTIFICATION', 'KEYWORD_RESPONSE'] as const;
const MEDIA_TYPES = ['', 'image', 'video', 'audio'] as const;

interface LangText {
  readonly messageText: string;
  readonly mediaUrl: string;
  readonly mediaType: string;
}

const EMPTY_LANG_TEXT: LangText = { messageText: '', mediaUrl: '', mediaType: '' };

export default function NewTemplatePage() {
  const router = useRouter();
  const params = useParams();
  const projectId = Number(params.id);
  const { addToast } = useToastStore();

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [type, setType] = useState<string>('STANDARD');
  const [en, setEn] = useState<LangText>(EMPTY_LANG_TEXT);
  const [es, setEs] = useState<LangText>(EMPTY_LANG_TEXT);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const backUrl = `/admin/projects/${projectId}/templates`;

  function buildTexts() {
    const texts: { language_id: number; message_text: string; media_url?: string; media_type?: string; quick_replies: Record<string, unknown>[] }[] = [];

    if (en.messageText.trim()) {
      texts.push({
        language_id: 1,
        message_text: en.messageText.trim(),
        media_url: en.mediaUrl.trim() || undefined,
        media_type: en.mediaType || undefined,
        quick_replies: [],
      });
    }

    if (es.messageText.trim()) {
      texts.push({
        language_id: 2,
        message_text: es.messageText.trim(),
        media_url: es.mediaUrl.trim() || undefined,
        media_type: es.mediaType || undefined,
        quick_replies: [],
      });
    }

    return texts;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();

    const texts = buildTexts();
    if (texts.length === 0) {
      addToast('error', 'At least one language must have message text');
      return;
    }

    setIsSubmitting(true);

    try {
      await templates.create({
        project_id: projectId,
        name,
        description: description || undefined,
        type,
        texts,
      });
      addToast('success', 'Template created successfully');
      router.push(backUrl);
    } catch (err) {
      const message =
        err instanceof ApiError && err.data
          ? (err.data as { detail?: string }).detail || 'Failed to create template'
          : 'Failed to create template';
      addToast('error', message);
    } finally {
      setIsSubmitting(false);
    }
  }

  function renderLangSection(
    label: string,
    langId: number,
    value: LangText,
    onChange: (updated: LangText) => void,
  ) {
    const prefix = langId === 1 ? 'en' : 'es';
    return (
      <div className="flex-1 border border-border rounded-lg overflow-hidden">
        <div className="px-4 py-2 bg-surface flex items-center gap-2">
          <Globe className="h-4 w-4 text-text-muted" />
          <span className="font-medium text-text">{label}</span>
        </div>
        <div className="p-4 space-y-4">
          <div>
            <label htmlFor={`${prefix}-message`} className="label">Message Text</label>
            <textarea
              id={`${prefix}-message`}
              value={value.messageText}
              onChange={(e) => onChange({ ...value, messageText: e.target.value })}
              className="input min-h-[100px] resize-y"
              placeholder={`Message in ${label}...`}
              rows={4}
            />
          </div>
          <div>
            <label htmlFor={`${prefix}-mediaUrl`} className="label">Media URL</label>
            <input
              id={`${prefix}-mediaUrl`}
              type="text"
              value={value.mediaUrl}
              onChange={(e) => onChange({ ...value, mediaUrl: e.target.value })}
              className="input"
              placeholder="https://..."
            />
          </div>
          <div>
            <label htmlFor={`${prefix}-mediaType`} className="label">Media Type</label>
            <select
              id={`${prefix}-mediaType`}
              value={value.mediaType}
              onChange={(e) => onChange({ ...value, mediaType: e.target.value })}
              className="input"
            >
              {MEDIA_TYPES.map((mt) => (
                <option key={mt} value={mt}>{mt || 'None'}</option>
              ))}
            </select>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <Header
        title="Create Template"
        description="Add a new message template to this project"
        actions={
          <Link href={backUrl} className="btn-secondary">
            <ArrowLeft className="h-4 w-4" />
            Back
          </Link>
        }
      />

      <div className="p-6 max-w-4xl">
        <form onSubmit={handleSubmit} className="card p-6 space-y-6">
          <div>
            <label htmlFor="name" className="label">
              Template Name <span className="text-error">*</span>
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input"
              placeholder="e.g., INTAKE_WELCOME"
              required
              autoFocus
            />
          </div>

          <div>
            <label htmlFor="description" className="label">Description</label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="input min-h-[80px] resize-y"
              placeholder="Brief description of this template..."
              rows={3}
            />
          </div>

          <div>
            <label htmlFor="type" className="label">Type</label>
            <select
              id="type"
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="input"
            >
              {TEMPLATE_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          <div>
            <h3 className="label mb-3">
              Localizations <span className="text-error">*</span>
            </h3>
            <div className="flex gap-4">
              {renderLangSection('English', 1, en, setEn)}
              {renderLangSection('Spanish', 2, es, setEs)}
            </div>
            <p className="text-caption text-text-muted mt-2">
              At least one language must have message text.
            </p>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-border">
            <Link href={backUrl} className="btn-secondary">Cancel</Link>
            <button type="submit" disabled={isSubmitting} className="btn-primary">
              <Plus className="h-4 w-4" />
              {isSubmitting ? 'Creating...' : 'Create Template'}
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
