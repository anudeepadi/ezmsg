'use client';

import { useState, useEffect, FormEvent } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { Header } from '@/components/layout';
import { projects, ApiError } from '@/lib/api';
import { useToastStore } from '@/lib/store';
import { ArrowLeft } from 'lucide-react';

export default function EditProjectPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = Number(params.id);
  const { addToast } = useToastStore();

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    async function loadProject() {
      try {
        const project = await projects.get(projectId);
        setName(project.name);
        setDescription(project.description || '');
      } catch {
        addToast('error', 'Failed to load project');
      } finally {
        setLoading(false);
      }
    }

    loadProject();
  }, [projectId, addToast]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      await projects.update(projectId, { name, description: description || undefined });
      addToast('success', 'Project updated successfully');
      router.push(`/admin/projects/${projectId}`);
    } catch (err) {
      const message =
        err instanceof ApiError && err.data
          ? (err.data as { detail?: string }).detail || 'Failed to update project'
          : 'Failed to update project';
      addToast('error', message);
    } finally {
      setIsSubmitting(false);
    }
  }

  if (loading) {
    return (
      <>
        <Header title="Loading..." />
        <div className="p-6">
          <div className="animate-pulse space-y-6">
            <div className="h-64 bg-surface rounded-lg" />
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Header
        title="Edit Project"
        description="Update project details"
        actions={
          <Link href={`/admin/projects/${projectId}`} className="btn-secondary">
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
              onChange={(e) => setName(e.target.value)}
              className="input"
              placeholder="e.g., QuitTxt Study 2025"
              required
              autoFocus
            />
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
            <Link href={`/admin/projects/${projectId}`} className="btn-secondary">
              Cancel
            </Link>
            <button type="submit" disabled={isSubmitting} className="btn-primary">
              {isSubmitting ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
