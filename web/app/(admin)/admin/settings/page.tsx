'use client';

import { Header } from '@/components/layout';
import { useAuthStore } from '@/lib/store';
import { User, Shield, Bell, Info } from 'lucide-react';

export default function SettingsPage() {
  const { user } = useAuthStore();

  return (
    <>
      <Header title="Settings" description="Account and system information" />

      <div className="p-6 space-y-6">
        {/* Profile Section */}
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-accent-light">
              <User className="h-5 w-5 text-accent" />
            </div>
            <h2 className="text-subtitle text-text">Profile</h2>
          </div>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="label">Email</label>
              <input
                type="text"
                className="input"
                value={user?.email ?? ''}
                readOnly
              />
            </div>
            <div>
              <label className="label">Full Name</label>
              <input
                type="text"
                className="input"
                value={user?.full_name ?? 'Not set'}
                readOnly
              />
            </div>
            <div>
              <label className="label">Role</label>
              <input
                type="text"
                className="input"
                value={user?.role ?? ''}
                readOnly
              />
            </div>
            <div>
              <label className="label">Status</label>
              <input
                type="text"
                className="input"
                value={user?.is_active ? 'Active' : 'Inactive'}
                readOnly
              />
            </div>
          </div>
        </div>

        {/* Security Section */}
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-warning-light">
              <Shield className="h-5 w-5 text-warning" />
            </div>
            <h2 className="text-subtitle text-text">Security</h2>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 rounded-lg bg-background">
              <div>
                <p className="text-body font-medium text-text">Password</p>
                <p className="text-body-sm text-text-secondary">
                  Contact admin to change password
                </p>
              </div>
            </div>
            <div className="flex items-center justify-between p-4 rounded-lg bg-background">
              <div>
                <p className="text-body font-medium text-text">Role</p>
                <p className="text-body-sm text-text-secondary">
                  Your current access level
                </p>
              </div>
              <span className="badge badge-success">{user?.role ?? 'Unknown'}</span>
            </div>
          </div>
        </div>

        {/* System Info Section */}
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-success-light">
              <Info className="h-5 w-5 text-success" />
            </div>
            <h2 className="text-subtitle text-text">System Info</h2>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 rounded-lg bg-background">
              <p className="text-body text-text">App Version</p>
              <p className="text-body font-medium text-text">1.0.0</p>
            </div>
            <div className="flex items-center justify-between p-4 rounded-lg bg-background">
              <p className="text-body text-text">Environment</p>
              <p className="text-body font-medium text-text">
                {process.env.NEXT_PUBLIC_ENV ?? 'Development'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
