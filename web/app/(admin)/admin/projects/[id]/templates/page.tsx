'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Header } from '@/components/layout';
import { templates, Template, ApiError } from '@/lib/api';
import { useToastStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import {
  ArrowLeft,
  Plus,
  Search,
  FileText,
  MessageSquare,
  Image,
  Globe,
  ChevronRight,
  Trash2,
} from 'lucide-react';

export default function TemplatesPage() {
  const params = useParams();
  const projectId = Number(params.id);
  const { addToast } = useToastStore();

  const [data, setData] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);

  useEffect(() => {
    loadTemplates();
  }, [projectId]);

  async function loadTemplates() {
    setLoading(true);
    try {
      const result = await templates.list(projectId);
      setData(result);
    } catch (err) {
      addToast('error', 'Failed to load templates');
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm('Are you sure you want to delete this template?')) return;

    try {
      await templates.delete(id);
      addToast('success', 'Template deleted');
      loadTemplates();
      if (selectedTemplate?.id === id) {
        setSelectedTemplate(null);
      }
    } catch (err) {
      addToast('error', 'Failed to delete template');
    }
  }

  const filteredTemplates = data.filter(
    (t) =>
      !search ||
      t.name.toLowerCase().includes(search.toLowerCase()) ||
      t.description?.toLowerCase().includes(search.toLowerCase())
  );

  // Group templates by prefix (INTAKE_, Q1_, Q2_, etc.)
  const groupedTemplates = filteredTemplates.reduce((acc, template) => {
    const prefix = template.name.split('_')[0] || 'Other';
    if (!acc[prefix]) acc[prefix] = [];
    acc[prefix].push(template);
    return acc;
  }, {} as Record<string, Template[]>);

  const getLanguageLabel = (langId: number) => {
    return langId === 1 ? 'EN' : langId === 2 ? 'ES' : `L${langId}`;
  };

  return (
    <>
      <Header
        title="Message Templates"
        description={`${data.length} templates in this project`}
        actions={
          <div className="flex items-center gap-3">
            <Link href={`/admin/projects/${projectId}`} className="btn-secondary">
              <ArrowLeft className="h-4 w-4" />
              Back
            </Link>
            <Link
              href={`/admin/projects/${projectId}/templates/new`}
              className="btn-primary"
            >
              <Plus className="h-4 w-4" />
              New Template
            </Link>
          </div>
        }
      />

      <div className="p-6">
        <div className="flex gap-6 h-[calc(100vh-200px)]">
          {/* Template List */}
          <div className="w-1/2 flex flex-col">
            {/* Search */}
            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
              <input
                type="text"
                placeholder="Search templates..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="input pl-10"
              />
            </div>

            {/* Template Groups */}
            <div className="card flex-1 overflow-y-auto">
              {loading ? (
                <div className="p-8 text-center">
                  <div className="animate-spin h-8 w-8 border-2 border-border border-t-primary rounded-full mx-auto" />
                </div>
              ) : filteredTemplates.length === 0 ? (
                <div className="p-8 text-center">
                  <FileText className="h-12 w-12 text-text-muted mx-auto mb-4" />
                  <p className="text-body text-text-secondary mb-4">
                    {search ? 'No templates match your search' : 'No templates yet'}
                  </p>
                  {!search && (
                    <Link
                      href={`/admin/projects/${projectId}/templates/new`}
                      className="btn-primary"
                    >
                      <Plus className="h-4 w-4" />
                      Create first template
                    </Link>
                  )}
                </div>
              ) : (
                <div className="divide-y divide-border">
                  {Object.entries(groupedTemplates).map(([group, templates]) => (
                    <div key={group}>
                      <div className="px-4 py-2 bg-background sticky top-0">
                        <h3 className="text-caption font-semibold text-text-muted uppercase tracking-wider">
                          {group} ({templates.length})
                        </h3>
                      </div>
                      {templates.map((template) => (
                        <button
                          key={template.id}
                          onClick={() => setSelectedTemplate(template)}
                          className={cn(
                            'w-full text-left px-4 py-3 hover:bg-surface transition-colors',
                            selectedTemplate?.id === template.id && 'bg-accent-light'
                          )}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3 min-w-0">
                              <MessageSquare className="h-4 w-4 text-text-muted flex-shrink-0" />
                              <div className="min-w-0">
                                <p className="font-medium text-text truncate">
                                  {template.name}
                                </p>
                                {template.description && (
                                  <p className="text-caption text-text-muted truncate">
                                    {template.description}
                                  </p>
                                )}
                              </div>
                            </div>
                            <div className="flex items-center gap-2 flex-shrink-0">
                              <div className="flex gap-1">
                                {template.texts.map((text) => (
                                  <span
                                    key={text.id}
                                    className={cn(
                                      'text-xs px-1.5 py-0.5 rounded',
                                      text.language_id === 1
                                        ? 'bg-blue-100 text-blue-700'
                                        : 'bg-orange-100 text-orange-700'
                                    )}
                                  >
                                    {getLanguageLabel(text.language_id)}
                                  </span>
                                ))}
                              </div>
                              <ChevronRight className="h-4 w-4 text-text-muted" />
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Template Preview */}
          <div className="w-1/2 card p-6 overflow-y-auto">
            {selectedTemplate ? (
              <div className="space-y-6">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-title text-text mb-1">{selectedTemplate.name}</h2>
                    {selectedTemplate.description && (
                      <p className="text-body text-text-secondary">
                        {selectedTemplate.description}
                      </p>
                    )}
                    <p className="text-caption text-text-muted mt-2">
                      Type: <span className="badge badge-default">{selectedTemplate.type}</span>
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Link
                      href={`/admin/projects/${projectId}/templates/${selectedTemplate.id}/edit`}
                      className="btn-secondary"
                    >
                      Edit
                    </Link>
                    <button
                      onClick={() => handleDelete(selectedTemplate.id)}
                      className="btn-ghost text-error"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                {/* Language Tabs */}
                {selectedTemplate.texts.length > 0 ? (
                  <div className="space-y-4">
                    {selectedTemplate.texts.map((text) => (
                      <div
                        key={text.id}
                        className="border border-border rounded-lg overflow-hidden"
                      >
                        <div className="px-4 py-2 bg-surface flex items-center gap-2">
                          <Globe className="h-4 w-4 text-text-muted" />
                          <span className="font-medium text-text">
                            {text.language_id === 1 ? 'English' : 'Spanish'}
                          </span>
                        </div>
                        <div className="p-4 space-y-4">
                          {/* Message Text */}
                          {text.message_text && (
                            <div>
                              <label className="text-caption text-text-muted block mb-1">
                                Message
                              </label>
                              <div className="bg-surface rounded-lg p-3 text-body text-text whitespace-pre-wrap">
                                {text.message_text}
                              </div>
                            </div>
                          )}

                          {/* Media */}
                          {text.media_url && (
                            <div>
                              <label className="text-caption text-text-muted block mb-1">
                                <Image className="h-3 w-3 inline mr-1" />
                                Media
                              </label>
                              <a
                                href={text.media_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-accent hover:underline text-body-sm break-all"
                              >
                                {text.media_url}
                              </a>
                            </div>
                          )}

                          {/* Quick Replies */}
                          {text.quick_replies && text.quick_replies.length > 0 && (
                            <div>
                              <label className="text-caption text-text-muted block mb-2">
                                Quick Replies
                              </label>
                              <div className="flex flex-wrap gap-2">
                                {text.quick_replies.map((reply, idx) => (
                                  <span
                                    key={idx}
                                    className="px-3 py-1.5 bg-accent text-white rounded-full text-body-sm"
                                  >
                                    {(reply as { label?: string }).label || String(reply)}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-text-muted">
                    No localizations configured for this template
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-text-muted">
                <MessageSquare className="h-12 w-12 mb-4 opacity-50" />
                <p className="text-body">Select a template to preview</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
