'use client';

import { useState, FormEvent } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { Header } from '@/components/layout';
import { variables, ApiError } from '@/lib/api';
import { useToastStore } from '@/lib/store';
import { ArrowLeft } from 'lucide-react';

const VARIABLE_TYPES = ['string', 'number', 'boolean', 'date', 'json'] as const;
const SOURCE_TYPES = ['system', 'user_input', 'calculated', 'external'] as const;

export default function NewVariablePage() {
  const router = useRouter();
  const params = useParams();
  const projectId = Number(params.id);
  const { addToast } = useToastStore();

  const [name, setName] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [description, setDescription] = useState('');
  const [type, setType] = useState<string>('string');
  const [sourceType, setSourceType] = useState<string>('system');
  const [defaultValue, setDefaultValue] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const backUrl = `/admin/projects/${projectId}/variables`;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      await variables.create({
        project_id: projectId,
        name,
        display_name: displayName || undefined,
        description: description || undefined,
        type,
        source_type: sourceType,
        default_value: defaultValue || undefined,
      });
      addToast('success', 'Variable created successfully');
      router.push(backUrl);
    } catch (err) {
      const message =
        err instanceof ApiError && err.data
          ? (err.data as { detail?: string }).detail || 'Failed to create variable'
          : 'Failed to create variable';
      addToast('error', message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <Header
        title="Create Variable"
        description="Add a new variable to this project"
        actions={
          <Link href={backUrl} className="btn-secondary">
            <ArrowLeft className="h-4 w-4" />
            Back
          </Link>
        }
      />

      <div className="p-6 max-w-2xl">
        <form onSubmit={handleSubmit} className="card p-6 space-y-6">
          <div>
            <label htmlFor="name" className="label">
              Name <span className="text-error">*</span>
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input"
              placeholder="e.g., participant_name"
              required
              autoFocus
            />
            <p className="text-caption text-text-muted mt-1.5">
              A unique identifier for this variable within the project.
            </p>
          </div>

          <div>
            <label htmlFor="displayName" className="label">Display Name</label>
            <input
              id="displayName"
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="input"
              placeholder="e.g., Participant Name"
            />
            <p className="text-caption text-text-muted mt-1.5">
              A human-readable label shown in the admin interface.
            </p>
          </div>

          <div>
            <label htmlFor="description" className="label">Description</label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="input min-h-[80px] resize-y"
              placeholder="What this variable is used for..."
              rows={3}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="type" className="label">Type</label>
              <select
                id="type"
                value={type}
                onChange={(e) => setType(e.target.value)}
                className="input"
              >
                {VARIABLE_TYPES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
              <p className="text-caption text-text-muted mt-1.5">
                The data type of the variable value.
              </p>
            </div>

            <div>
              <label htmlFor="sourceType" className="label">Source Type</label>
              <select
                id="sourceType"
                value={sourceType}
                onChange={(e) => setSourceType(e.target.value)}
                className="input"
              >
                {SOURCE_TYPES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
              <p className="text-caption text-text-muted mt-1.5">
                How this variable gets its value.
              </p>
            </div>
          </div>

          <div>
            <label htmlFor="defaultValue" className="label">Default Value</label>
            <input
              id="defaultValue"
              type="text"
              value={defaultValue}
              onChange={(e) => setDefaultValue(e.target.value)}
              className="input"
              placeholder="Optional default value"
            />
            <p className="text-caption text-text-muted mt-1.5">
              Value used when no explicit value has been set for a participant.
            </p>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-border">
            <Link href={backUrl} className="btn-secondary">Cancel</Link>
            <button type="submit" disabled={isSubmitting} className="btn-primary">
              {isSubmitting ? 'Creating...' : 'Create Variable'}
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
