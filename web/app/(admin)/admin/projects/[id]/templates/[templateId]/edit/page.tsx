"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { Header } from "@/components/layout";
import { templates, ApiError } from "@/lib/api";
import { useToastStore } from "@/lib/store";
import { ArrowLeft } from "lucide-react";

interface LangText {
  message_text: string;
  media_url: string;
  media_type: string;
}

const emptyLangText: LangText = { message_text: "", media_url: "", media_type: "" };

export default function EditTemplatePage() {
  const router = useRouter();
  const params = useParams();
  const projectId = Number(params.id);
  const templateId = Number(params.templateId);
  const { addToast } = useToastStore();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [type, setType] = useState("text");
  const [enText, setEnText] = useState<LangText>({ ...emptyLangText });
  const [esText, setEsText] = useState<LangText>({ ...emptyLangText });
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const backUrl = `/admin/projects/${projectId}/templates`;

  useEffect(() => {
    async function loadTemplate() {
      try {
        const tmpl = await templates.get(templateId);
        setName(tmpl.name);
        setDescription(tmpl.description || "");
        setType(tmpl.type);

        const en = tmpl.texts.find((t) => t.language_id === 1);
        if (en) {
          setEnText({
            message_text: en.message_text || "",
            media_url: en.media_url || "",
            media_type: en.media_type || "",
          });
        }

        const es = tmpl.texts.find((t) => t.language_id === 2);
        if (es) {
          setEsText({
            message_text: es.message_text || "",
            media_url: es.media_url || "",
            media_type: es.media_type || "",
          });
        }
      } catch {
        addToast("error", "Failed to load template");
      } finally {
        setLoading(false);
      }
    }
    loadTemplate();
  }, [templateId, addToast]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);

    const texts: {
      language_id: number;
      message_text: string;
      media_url?: string;
      media_type?: string;
    }[] = [];

    if (enText.message_text.trim()) {
      texts.push({
        language_id: 1,
        message_text: enText.message_text,
        media_url: enText.media_url || undefined,
        media_type: enText.media_type || undefined,
      });
    }

    if (esText.message_text.trim()) {
      texts.push({
        language_id: 2,
        message_text: esText.message_text,
        media_url: esText.media_url || undefined,
        media_type: esText.media_type || undefined,
      });
    }

    try {
      await templates.update(templateId, {
        name,
        description: description || undefined,
        type,
        texts,
      });
      addToast("success", "Template updated successfully");
      router.push(backUrl);
    } catch (err) {
      const message =
        err instanceof ApiError && err.data
          ? (err.data as { detail?: string }).detail ||
            "Failed to update template"
          : "Failed to update template";
      addToast("error", message);
    } finally {
      setIsSubmitting(false);
    }
  }

  if (loading) {
    return (
      <>
        <Header title="Edit Template" />
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
        title="Edit Template"
        description={name}
        actions={
          <Link href={backUrl} className="btn-secondary">
            <ArrowLeft className="h-4 w-4" />
            Back
          </Link>
        }
      />

      <div className="p-6 max-w-4xl">
        <form onSubmit={handleSubmit} className="card p-6 space-y-6">
          <div className="grid grid-cols-2 gap-4">
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
                required
              />
            </div>

            <div>
              <label htmlFor="type" className="label">
                Type
              </label>
              <select
                id="type"
                value={type}
                onChange={(e) => setType(e.target.value)}
                className="input"
              >
                <option value="text">Text</option>
                <option value="media">Media</option>
                <option value="interactive">Interactive</option>
              </select>
            </div>
          </div>

          <div>
            <label htmlFor="description" className="label">
              Description
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="input min-h-[60px] resize-y"
              rows={2}
            />
          </div>

          {/* Localizations */}
          <div className="border-t border-border pt-6">
            <h3 className="text-title text-text mb-4">Localizations</h3>
            <div className="grid grid-cols-2 gap-6">
              {/* English */}
              <div className="space-y-4">
                <h4 className="text-body font-medium text-text">English</h4>
                <div>
                  <label className="label">Message Text</label>
                  <textarea
                    value={enText.message_text}
                    onChange={(e) =>
                      setEnText({ ...enText, message_text: e.target.value })
                    }
                    className="input min-h-[100px] resize-y"
                    rows={4}
                    placeholder="English message content..."
                  />
                </div>
                <div>
                  <label className="label">Media URL</label>
                  <input
                    type="text"
                    value={enText.media_url}
                    onChange={(e) =>
                      setEnText({ ...enText, media_url: e.target.value })
                    }
                    className="input"
                    placeholder="https://..."
                  />
                </div>
                <div>
                  <label className="label">Media Type</label>
                  <select
                    value={enText.media_type}
                    onChange={(e) =>
                      setEnText({ ...enText, media_type: e.target.value })
                    }
                    className="input"
                  >
                    <option value="">None</option>
                    <option value="image">Image</option>
                    <option value="video">Video</option>
                    <option value="audio">Audio</option>
                    <option value="document">Document</option>
                  </select>
                </div>
              </div>

              {/* Spanish */}
              <div className="space-y-4">
                <h4 className="text-body font-medium text-text">Spanish</h4>
                <div>
                  <label className="label">Message Text</label>
                  <textarea
                    value={esText.message_text}
                    onChange={(e) =>
                      setEsText({ ...esText, message_text: e.target.value })
                    }
                    className="input min-h-[100px] resize-y"
                    rows={4}
                    placeholder="Spanish message content..."
                  />
                </div>
                <div>
                  <label className="label">Media URL</label>
                  <input
                    type="text"
                    value={esText.media_url}
                    onChange={(e) =>
                      setEsText({ ...esText, media_url: e.target.value })
                    }
                    className="input"
                    placeholder="https://..."
                  />
                </div>
                <div>
                  <label className="label">Media Type</label>
                  <select
                    value={esText.media_type}
                    onChange={(e) =>
                      setEsText({ ...esText, media_type: e.target.value })
                    }
                    className="input"
                  >
                    <option value="">None</option>
                    <option value="image">Image</option>
                    <option value="video">Video</option>
                    <option value="audio">Audio</option>
                    <option value="document">Document</option>
                  </select>
                </div>
              </div>
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
