"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { Header } from "@/components/layout";
import { nodes, templates, Template, ApiError } from "@/lib/api";
import { useToastStore } from "@/lib/store";
import { ArrowLeft } from "lucide-react";

export default function NewNodePage() {
  const router = useRouter();
  const params = useParams();
  const projectId = Number(params.id);
  const { addToast } = useToastStore();

  const [name, setName] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [description, setDescription] = useState("");
  const [nodeOrder, setNodeOrder] = useState(0);
  const [templateId, setTemplateId] = useState<number | null>(null);
  const [isEntryNode, setIsEntryNode] = useState(false);
  const [isTerminalNode, setIsTerminalNode] = useState(false);
  const [templateList, setTemplateList] = useState<Template[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const backUrl = `/admin/projects/${projectId}/nodes`;

  useEffect(() => {
    templates.list(projectId).then(setTemplateList).catch(() => {});
  }, [projectId]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      await nodes.create({
        project_id: projectId,
        name,
        display_name: displayName || undefined,
        description: description || undefined,
        node_order: nodeOrder,
        template_id: templateId ?? undefined,
        is_entry_node: isEntryNode,
        is_terminal_node: isTerminalNode,
      });
      addToast("success", "Node created successfully");
      router.push(backUrl);
    } catch (err) {
      const message =
        err instanceof ApiError && err.data
          ? (err.data as { detail?: string }).detail || "Failed to create node"
          : "Failed to create node";
      addToast("error", message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <Header
        title="Create Node"
        description="Add a new messaging node to the protocol"
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
              Node Name <span className="text-error">*</span>
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input font-mono"
              placeholder="e.g., INTAKE_WELCOME"
              required
              autoFocus
            />
            <p className="text-caption text-text-muted mt-1.5">
              Internal identifier. Use UPPERCASE_SNAKE_CASE convention.
            </p>
          </div>

          <div>
            <label htmlFor="displayName" className="label">
              Display Name
            </label>
            <input
              id="displayName"
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="input"
              placeholder="e.g., Welcome Message"
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
              className="input min-h-[80px] resize-y"
              placeholder="What this node does in the protocol flow..."
              rows={3}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="nodeOrder" className="label">
                Node Order
              </label>
              <input
                id="nodeOrder"
                type="number"
                value={nodeOrder}
                onChange={(e) => setNodeOrder(Number(e.target.value))}
                className="input"
                min={0}
              />
            </div>

            <div>
              <label htmlFor="templateId" className="label">
                Template
              </label>
              <select
                id="templateId"
                value={templateId ?? ""}
                onChange={(e) =>
                  setTemplateId(e.target.value ? Number(e.target.value) : null)
                }
                className="input"
              >
                <option value="">None</option>
                {templateList.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <input
                id="isEntryNode"
                type="checkbox"
                checked={isEntryNode}
                onChange={(e) => setIsEntryNode(e.target.checked)}
                className="h-4 w-4 rounded border-border"
              />
              <label htmlFor="isEntryNode" className="label !mb-0">
                Entry Node
              </label>
            </div>

            <div className="flex items-center gap-3">
              <input
                id="isTerminalNode"
                type="checkbox"
                checked={isTerminalNode}
                onChange={(e) => setIsTerminalNode(e.target.checked)}
                className="h-4 w-4 rounded border-border"
              />
              <label htmlFor="isTerminalNode" className="label !mb-0">
                Terminal Node
              </label>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-border">
            <Link href={backUrl} className="btn-secondary">
              Cancel
            </Link>
            <button
              type="submit"
              disabled={isSubmitting}
              className="btn-primary"
            >
              {isSubmitting ? "Creating..." : "Create Node"}
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
