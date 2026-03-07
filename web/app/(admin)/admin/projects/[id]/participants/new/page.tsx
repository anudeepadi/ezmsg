'use client';

import { useState, FormEvent } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { Header } from '@/components/layout';
import { participants, ApiError } from '@/lib/api';
import { useToastStore } from '@/lib/store';
import { ArrowLeft } from 'lucide-react';

export default function NewParticipantPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = Number(params.id);
  const { addToast } = useToastStore();

  const [externalId, setExternalId] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [channelType, setChannelType] = useState('MOBILE_APP');
  const [languageId, setLanguageId] = useState(1);
  const [timezone, setTimezone] = useState('America/Chicago');
  const [isTestParticipant, setIsTestParticipant] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const backUrl = `/admin/projects/${projectId}/participants`;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      await participants.create({
        project_id: projectId,
        external_id: externalId || undefined,
        phone_number: phoneNumber || undefined,
        channel_type: channelType,
        language_id: languageId,
        is_test_participant: isTestParticipant,
      });
      addToast('success', 'Participant created successfully');
      router.push(backUrl);
    } catch (err) {
      const message =
        err instanceof ApiError && err.data
          ? (err.data as { detail?: string }).detail || 'Failed to create participant'
          : 'Failed to create participant';
      addToast('error', message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <Header
        title="Create Participant"
        description="Enroll a new participant in this project"
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
            <label htmlFor="externalId" className="label">External ID</label>
            <input
              id="externalId"
              type="text"
              value={externalId}
              onChange={(e) => setExternalId(e.target.value)}
              className="input"
              placeholder="e.g., SUBJ-001"
            />
            <p className="text-caption text-text-muted mt-1.5">
              Optional identifier used by researchers to track this participant.
            </p>
          </div>

          <div>
            <label htmlFor="phoneNumber" className="label">Phone Number</label>
            <input
              id="phoneNumber"
              type="tel"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              className="input"
              placeholder="e.g., +15551234567"
            />
            <p className="text-caption text-text-muted mt-1.5">
              Required for SMS delivery via Twilio.
            </p>
          </div>

          <div>
            <label htmlFor="channelType" className="label">Channel Type</label>
            <select
              id="channelType"
              value={channelType}
              onChange={(e) => setChannelType(e.target.value)}
              className="input"
            >
              <option value="MOBILE_APP">Mobile App</option>
              <option value="TWILIO">Twilio SMS</option>
              <option value="EMAIL">Email</option>
              <option value="FACEBOOK">Facebook</option>
            </select>
          </div>

          <div>
            <label htmlFor="languageId" className="label">Language</label>
            <select
              id="languageId"
              value={languageId}
              onChange={(e) => setLanguageId(Number(e.target.value))}
              className="input"
            >
              <option value={1}>English</option>
              <option value={2}>Spanish</option>
            </select>
          </div>

          <div>
            <label htmlFor="timezone" className="label">Timezone</label>
            <input
              id="timezone"
              type="text"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              className="input"
              placeholder="America/Chicago"
            />
          </div>

          <div className="flex items-center gap-3">
            <input
              id="isTestParticipant"
              type="checkbox"
              checked={isTestParticipant}
              onChange={(e) => setIsTestParticipant(e.target.checked)}
              className="h-4 w-4 rounded border-border"
            />
            <label htmlFor="isTestParticipant" className="label !mb-0">
              Test Participant
            </label>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-border">
            <Link href={backUrl} className="btn-secondary">Cancel</Link>
            <button type="submit" disabled={isSubmitting} className="btn-primary">
              {isSubmitting ? 'Creating...' : 'Create Participant'}
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
