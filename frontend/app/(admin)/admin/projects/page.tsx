'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Header } from '@/components/layout';
import { projects, Project, ApiError } from '@/lib/api';
import { useToastStore } from '@/lib/store';
import { formatDate, getStatusVariant, cn } from '@/lib/utils';
import {
  Plus,
  Search,
  MoreHorizontal,
  Pencil,
  Trash2,
  Play,
  Pause,
  ArrowRight,
} from 'lucide-react';

export default function ProjectsPage() {
  const [projectList, setProjectList] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [openMenu, setOpenMenu] = useState<number | null>(null);
  const { addToast } = useToastStore();

  useEffect(() => {
    loadProjects();
  }, []);

  async function loadProjects() {
    try {
      const response = await projects.list();
      setProjectList(response.items);
    } catch (err) {
      addToast('error', 'Failed to load projects');
    } finally {
      setLoading(false);
    }
  }

  async function handleActivate(id: number) {
    try {
      await projects.activate(id);
      addToast('success', 'Project activated');
      loadProjects();
    } catch (err) {
      addToast('error', 'Failed to activate project');
    }
    setOpenMenu(null);
  }

  async function handleSuspend(id: number) {
    try {
      await projects.suspend(id);
      addToast('success', 'Project suspended');
      loadProjects();
    } catch (err) {
      addToast('error', 'Failed to suspend project');
    }
    setOpenMenu(null);
  }

  async function handleDelete(id: number) {
    if (!confirm('Are you sure you want to delete this project?')) return;

    try {
      await projects.delete(id);
      addToast('success', 'Project deleted');
      loadProjects();
    } catch (err) {
      addToast('error', 'Failed to delete project');
    }
    setOpenMenu(null);
  }

  const filteredProjects = projectList.filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      (p.uu_id && p.uu_id.toLowerCase().includes(search.toLowerCase())) ||
      p.owner_email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <>
      <Header
        title="Projects"
        description="Manage your messaging protocols"
        actions={
          <Link href="/admin/projects/new" className="btn-primary">
            <Plus className="h-4 w-4" />
            New Project
          </Link>
        }
      />

      <div className="p-6">
        {/* Search */}
        <div className="mb-6">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
            <input
              type="text"
              placeholder="Search projects..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input pl-10"
            />
          </div>
        </div>

        {/* Table */}
        <div className="card overflow-hidden">
          {loading ? (
            <div className="p-8 text-center">
              <div className="animate-spin h-8 w-8 border-2 border-border border-t-primary rounded-full mx-auto" />
            </div>
          ) : filteredProjects.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-body text-text-secondary mb-4">
                {search ? 'No projects match your search' : 'No projects yet'}
              </p>
              {!search && (
                <Link href="/admin/projects/new" className="btn-primary">
                  <Plus className="h-4 w-4" />
                  Create your first project
                </Link>
              )}
            </div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Project</th>
                  <th>UUID</th>
                  <th>Owner</th>
                  <th>Status</th>
                  <th>Participants</th>
                  <th>Nodes</th>
                  <th className="w-10"></th>
                </tr>
              </thead>
              <tbody>
                {filteredProjects.map((project) => (
                  <tr key={project.id}>
                    <td>
                      <Link
                        href={`/admin/projects/${project.id}`}
                        className="font-medium text-text hover:text-accent transition-colors"
                      >
                        {project.name}
                      </Link>
                      {project.description && (
                        <p className="text-caption text-text-muted truncate max-w-xs">
                          {project.description}
                        </p>
                      )}
                    </td>
                    <td>
                      <code className="text-body-sm font-mono bg-background px-2 py-0.5 rounded">
                        {project.uu_id || '-'}
                      </code>
                    </td>
                    <td className="text-text-secondary">
                      {project.owner_email}
                    </td>
                    <td>
                      <span
                        className={cn('badge', {
                          'badge-success': getStatusVariant(project.status) === 'success',
                          'badge-warning': getStatusVariant(project.status) === 'warning',
                          'badge-error': getStatusVariant(project.status) === 'error',
                          'badge-default': getStatusVariant(project.status) === 'default',
                        })}
                      >
                        {project.status}
                      </span>
                    </td>
                    <td>{project.participant_count || 0}</td>
                    <td>{project.node_count || 0}</td>
                    <td>
                      <div className="relative">
                        <button
                          onClick={() =>
                            setOpenMenu(openMenu === project.id ? null : project.id)
                          }
                          className="btn-ghost p-2"
                        >
                          <MoreHorizontal className="h-4 w-4" />
                        </button>

                        {openMenu === project.id && (
                          <>
                            <div
                              className="fixed inset-0 z-10"
                              onClick={() => setOpenMenu(null)}
                            />
                            <div className="absolute right-0 top-full mt-1 w-48 bg-surface border border-border rounded-lg shadow-elevated z-20 py-1">
                              <Link
                                href={`/admin/projects/${project.id}`}
                                className="flex items-center gap-2 px-4 py-2 text-body-sm text-text hover:bg-background transition-colors"
                              >
                                <ArrowRight className="h-4 w-4" />
                                View Details
                              </Link>
                              <Link
                                href={`/admin/projects/${project.id}/edit`}
                                className="flex items-center gap-2 px-4 py-2 text-body-sm text-text hover:bg-background transition-colors"
                              >
                                <Pencil className="h-4 w-4" />
                                Edit
                              </Link>
                              <div className="border-t border-border my-1" />
                              {project.status === 'ACTIVE' ? (
                                <button
                                  onClick={() => handleSuspend(project.id)}
                                  className="flex items-center gap-2 px-4 py-2 text-body-sm text-warning hover:bg-background transition-colors w-full text-left"
                                >
                                  <Pause className="h-4 w-4" />
                                  Suspend
                                </button>
                              ) : (
                                <button
                                  onClick={() => handleActivate(project.id)}
                                  className="flex items-center gap-2 px-4 py-2 text-body-sm text-success hover:bg-background transition-colors w-full text-left"
                                >
                                  <Play className="h-4 w-4" />
                                  Activate
                                </button>
                              )}
                              <button
                                onClick={() => handleDelete(project.id)}
                                className="flex items-center gap-2 px-4 py-2 text-body-sm text-error hover:bg-background transition-colors w-full text-left"
                              >
                                <Trash2 className="h-4 w-4" />
                                Delete
                              </button>
                            </div>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </>
  );
}
