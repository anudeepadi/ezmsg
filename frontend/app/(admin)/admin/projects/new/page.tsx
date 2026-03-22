'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Header } from '@/components/layout';
import { projects, ApiError } from '@/lib/api';
import { useToastStore } from '@/lib/store';
import { ArrowLeft } from 'lucide-react';

export default function NewProjectPage() {
  const router = useRouter();
  const { addToast } = useToastStore();

  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Auto-generate code from name
  const handleNameChange = (value: string) => {
    setName(value);
    if (!code || code === generateCode(name)) {
      setCode(generateCode(value));
    }
  };

  function generateCode(name: string) {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '')
      .slice(0, 32);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const project = await projects.create({ name, code, description: description || undefined });
      addToast('success', 'Project created successfully');
      router.push(`/admin/projects/${project.id}`);
    } catch (err) {
      const message =
        err instanceof ApiError && err.data
          ? (err.data as { detail?: string }).detail || 'Failed to create project'
          : 'Failed to create project';
      addToast('error', message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <Header
        title="Create Project"
        description="Set up a new messaging protocol"
        actions={
          <Link href="/admin/projects" className="btn-secondary">
            <ArrowLeft className="h-4 w-4" />
            Back
          </Link>
        }
      />

      <div className="p-6 max-w-2xl">
        <form onSubmit={handleSubmit} className="card p-6 space-y-6">
          <div>
            <label htmlFor="name" className="label">
              Project Name <span className="text-error">*</span>
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => handleNameChange(e.target.value)}
              className="input"
              placeholder="e.g., QuitTxt Study 2025"
              required
              autoFocus
            />
          </div>

          <div>
            <label htmlFor="code" className="label">
              Project Code <span className="text-error">*</span>
            </label>
            <input
              id="code"
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="input font-mono"
              placeholder="e.g., quittxt-2025"
              required
              pattern="[a-z0-9-]+"
            />
            <p className="text-caption text-text-muted mt-1.5">
              Used for API identification. Lowercase letters, numbers, and hyphens only.
            </p>
          </div>

          <div>
            <label htmlFor="description" className="label">
              Description
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="input min-h-[100px] resize-y"
              placeholder="Brief description of the messaging protocol..."
              rows={4}
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-border">
            <Link href="/admin/projects" className="btn-secondary">
              Cancel
            </Link>
            <button type="submit" disabled={isSubmitting} className="btn-primary">
              {isSubmitting ? 'Creating...' : 'Create Project'}
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
