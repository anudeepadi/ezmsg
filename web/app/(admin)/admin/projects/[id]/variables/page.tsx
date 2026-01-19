'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Header } from '@/components/layout';
import { variables, Variable, VariableCreate, ApiError } from '@/lib/api';
import { useToastStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import {
  ArrowLeft,
  Plus,
  Search,
  Variable as VariableIcon,
  Trash2,
  Edit2,
  Save,
  X,
  Hash,
  Calendar,
  ToggleLeft,
  Type,
  Calculator,
} from 'lucide-react';

const variableTypes = [
  { value: 'STRING', label: 'String', icon: Type },
  { value: 'INTEGER', label: 'Integer', icon: Hash },
  { value: 'DECIMAL', label: 'Decimal', icon: Calculator },
  { value: 'DATETIME', label: 'Date/Time', icon: Calendar },
  { value: 'BOOLEAN', label: 'Boolean', icon: ToggleLeft },
];

const sourceTypes = [
  { value: 'MANUAL', label: 'Manual' },
  { value: 'CALCULATED', label: 'Calculated' },
  { value: 'EXTERNAL', label: 'External' },
  { value: 'SYSTEM', label: 'System' },
];

interface EditingVariable {
  id?: number;
  name: string;
  display_name: string;
  description: string;
  type: string;
  source_type: string;
  default_value: string;
}

export default function VariablesPage() {
  const params = useParams();
  const projectId = Number(params.id);
  const { addToast } = useToastStore();

  const [data, setData] = useState<Variable[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [editing, setEditing] = useState<EditingVariable | null>(null);
  const [showNewForm, setShowNewForm] = useState(false);

  useEffect(() => {
    loadVariables();
  }, [projectId]);

  async function loadVariables() {
    setLoading(true);
    try {
      const result = await variables.list(projectId);
      setData(result);
    } catch (err) {
      addToast('error', 'Failed to load variables');
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    if (!editing) return;

    try {
      if (editing.id) {
        await variables.update(editing.id, {
          name: editing.name,
          display_name: editing.display_name || undefined,
          description: editing.description || undefined,
          type: editing.type,
          default_value: editing.default_value || undefined,
        });
        addToast('success', 'Variable updated');
      } else {
        await variables.create({
          project_id: projectId,
          name: editing.name,
          display_name: editing.display_name || undefined,
          description: editing.description || undefined,
          type: editing.type,
          source_type: editing.source_type,
          default_value: editing.default_value || undefined,
        });
        addToast('success', 'Variable created');
      }
      setEditing(null);
      setShowNewForm(false);
      loadVariables();
    } catch (err) {
      const error = err as ApiError;
      const errorData = error.data as { detail?: string } | undefined;
      addToast('error', errorData?.detail || 'Failed to save variable');
    }
  }

  async function handleDelete(id: number) {
    if (!confirm('Are you sure you want to delete this variable?')) return;

    try {
      await variables.delete(id);
      addToast('success', 'Variable deleted');
      loadVariables();
    } catch (err) {
      addToast('error', 'Failed to delete variable');
    }
  }

  function startNew() {
    setEditing({
      name: '',
      display_name: '',
      description: '',
      type: 'STRING',
      source_type: 'MANUAL',
      default_value: '',
    });
    setShowNewForm(true);
  }

  function startEdit(variable: Variable) {
    setEditing({
      id: variable.id,
      name: variable.name,
      display_name: variable.display_name || '',
      description: variable.description || '',
      type: variable.type,
      source_type: variable.source_type,
      default_value: variable.default_value || '',
    });
    setShowNewForm(false);
  }

  const filteredVariables = data.filter(
    (v) =>
      !search ||
      v.name.toLowerCase().includes(search.toLowerCase()) ||
      v.display_name?.toLowerCase().includes(search.toLowerCase())
  );

  const getTypeIcon = (type: string) => {
    const found = variableTypes.find((t) => t.value === type);
    return found ? found.icon : Type;
  };

  return (
    <>
      <Header
        title="Variables"
        description={`${data.length} variables defined`}
        actions={
          <div className="flex items-center gap-3">
            <Link href={`/admin/projects/${projectId}`} className="btn-secondary">
              <ArrowLeft className="h-4 w-4" />
              Back
            </Link>
            <button onClick={startNew} className="btn-primary">
              <Plus className="h-4 w-4" />
              New Variable
            </button>
          </div>
        }
      />

      <div className="p-6">
        {/* Search */}
        <div className="relative mb-6 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
          <input
            type="text"
            placeholder="Search variables..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input pl-10"
          />
        </div>

        <div className="flex gap-6">
          {/* Variables List */}
          <div className={cn('card overflow-hidden', showNewForm || editing ? 'w-1/2' : 'w-full')}>
            {loading ? (
              <div className="p-8 text-center">
                <div className="animate-spin h-8 w-8 border-2 border-border border-t-primary rounded-full mx-auto" />
              </div>
            ) : filteredVariables.length === 0 ? (
              <div className="p-8 text-center">
                <VariableIcon className="h-12 w-12 text-text-muted mx-auto mb-4" />
                <p className="text-body text-text-secondary mb-4">
                  {search ? 'No variables match your search' : 'No variables defined yet'}
                </p>
                {!search && (
                  <button onClick={startNew} className="btn-primary">
                    <Plus className="h-4 w-4" />
                    Create first variable
                  </button>
                )}
              </div>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Variable</th>
                    <th>Type</th>
                    <th>Source</th>
                    <th>Default</th>
                    <th className="w-24"></th>
                  </tr>
                </thead>
                <tbody>
                  {filteredVariables.map((variable) => {
                    const TypeIcon = getTypeIcon(variable.type);
                    return (
                      <tr
                        key={variable.id}
                        className={cn(
                          editing?.id === variable.id && 'bg-accent-light'
                        )}
                      >
                        <td>
                          <div className="flex items-center gap-3">
                            <div className="p-1.5 bg-surface rounded">
                              <TypeIcon className="h-4 w-4 text-text-muted" />
                            </div>
                            <div>
                              <p className="font-mono font-medium text-text">
                                {`{{${variable.name}}}`}
                              </p>
                              {variable.display_name && (
                                <p className="text-caption text-text-muted">
                                  {variable.display_name}
                                </p>
                              )}
                            </div>
                          </div>
                        </td>
                        <td>
                          <span className="badge badge-default">{variable.type}</span>
                        </td>
                        <td>
                          <span
                            className={cn('badge', {
                              'badge-success': variable.source_type === 'SYSTEM',
                              'badge-warning': variable.source_type === 'CALCULATED',
                              'badge-default': variable.source_type === 'MANUAL',
                            })}
                          >
                            {variable.source_type}
                          </span>
                        </td>
                        <td className="text-text-secondary font-mono text-body-sm">
                          {variable.default_value || '-'}
                        </td>
                        <td>
                          <div className="flex justify-end gap-1">
                            <button
                              onClick={() => startEdit(variable)}
                              className="btn-ghost p-1.5"
                              title="Edit"
                            >
                              <Edit2 className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(variable.id)}
                              className="btn-ghost p-1.5 text-error"
                              title="Delete"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>

          {/* Edit Form */}
          {(showNewForm || editing) && (
            <div className="w-1/2 card p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-title text-text">
                  {editing?.id ? 'Edit Variable' : 'New Variable'}
                </h3>
                <button
                  onClick={() => {
                    setEditing(null);
                    setShowNewForm(false);
                  }}
                  className="btn-ghost p-1.5"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="label">
                    Variable Name <span className="text-error">*</span>
                  </label>
                  <input
                    type="text"
                    value={editing?.name || ''}
                    onChange={(e) =>
                      setEditing((prev) =>
                        prev ? { ...prev, name: e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, '_') } : prev
                      )
                    }
                    className="input font-mono"
                    placeholder="e.g., quit_date"
                  />
                  <p className="text-caption text-text-muted mt-1">
                    Use in templates as: {`{{${editing?.name || 'variable_name'}}}`}
                  </p>
                </div>

                <div>
                  <label className="label">Display Name</label>
                  <input
                    type="text"
                    value={editing?.display_name || ''}
                    onChange={(e) =>
                      setEditing((prev) =>
                        prev ? { ...prev, display_name: e.target.value } : prev
                      )
                    }
                    className="input"
                    placeholder="e.g., Quit Date"
                  />
                </div>

                <div>
                  <label className="label">Description</label>
                  <textarea
                    value={editing?.description || ''}
                    onChange={(e) =>
                      setEditing((prev) =>
                        prev ? { ...prev, description: e.target.value } : prev
                      )
                    }
                    className="input"
                    rows={2}
                    placeholder="What this variable is used for..."
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="label">Type</label>
                    <select
                      value={editing?.type || 'STRING'}
                      onChange={(e) =>
                        setEditing((prev) =>
                          prev ? { ...prev, type: e.target.value } : prev
                        )
                      }
                      className="input"
                    >
                      {variableTypes.map((type) => (
                        <option key={type.value} value={type.value}>
                          {type.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="label">Source</label>
                    <select
                      value={editing?.source_type || 'MANUAL'}
                      onChange={(e) =>
                        setEditing((prev) =>
                          prev ? { ...prev, source_type: e.target.value } : prev
                        )
                      }
                      className="input"
                      disabled={!!editing?.id}
                    >
                      {sourceTypes.map((source) => (
                        <option key={source.value} value={source.value}>
                          {source.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="label">Default Value</label>
                  <input
                    type="text"
                    value={editing?.default_value || ''}
                    onChange={(e) =>
                      setEditing((prev) =>
                        prev ? { ...prev, default_value: e.target.value } : prev
                      )
                    }
                    className="input font-mono"
                    placeholder="Optional default value"
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-border">
                  <button
                    onClick={() => {
                      setEditing(null);
                      setShowNewForm(false);
                    }}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={!editing?.name}
                    className="btn-primary"
                  >
                    <Save className="h-4 w-4" />
                    {editing?.id ? 'Update' : 'Create'}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
