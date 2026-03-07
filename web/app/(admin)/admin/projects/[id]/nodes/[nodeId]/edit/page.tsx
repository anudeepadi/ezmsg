"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { Header } from "@/components/layout";
import { nodes, templates, Template, ApiError } from "@/lib/api";
import { useToastStore } from "@/lib/store";
import { ArrowLeft } from "lucide-react";

export default function EditNodePage() {
  const router = useRouter();
  const params = useParams();
  const projectId = Number(params.id);
  const nodeId = Number(params.nodeId);
  const { addToast } = useToastStore();

  const [name, setName] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [description, setDescription] = useState("");
  const [nodeOrder, setNodeOrder] = useState(0);
  const [templateId, setTemplateId] = useState<number | null>(null);
  const [isEntryNode, setIsEntryNode] = useState(false);
  const [isTerminalNode, setIsTerminalNode] = useState(false);
  const [templateList, setTemplateList] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const backUrl = `/admin/projects/${projectId}/nodes`;

  useEffect(() => {
    async function loadData() {
      try {
        const [node, tmpls] = await Promise.all([
          nodes.get(nodeId),
          templates.list(projectId),
        ]);
        setName(node.name);
        setDisplayName(node.display_name || "");
        setDescription(node.description || "");
        setNodeOrder(node.node_order);
        setTemplateId(node.template_id);
        setIsEntryNode(node.is_entry_node);
        setIsTerminalNode(node.is_terminal_node);
        setTemplateList(tmpls);
      } catch {
        addToast("error", "Failed to load node");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [nodeId, projectId, addToast]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      await nodes.update(nodeId, {
        name,
        display_name: displayName || undefined,
        description: description || undefined,
        node_order: nodeOrder,
        template_id: templateId ?? undefined,
        is_entry_node: isEntryNode,
        is_terminal_node: isTerminalNode,
      });
      addToast("success", "Node updated successfully");
      router.push(backUrl);
    } catch (err) {
      const message =
        err instanceof ApiError && err.data
          ? (err.data as { detail?: string }).detail || "Failed to update node"
          : "Failed to update node";
      addToast("error", message);
    } finally {
      setIsSubmitting(false);
    }
  }

  if (loading) {
    return (
      <>
        <Header title="Edit Node" />
        <div className="p-6">
          <div className="card p-8 text-center">
            <div className="animate-spin h-8 w-8 border-2 border-border border-t-primary rounded-full mx-auto" />
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Header
        title="Edit Node"
        description={displayName || name}
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
              required
            />
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
              {isSubmitting ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
