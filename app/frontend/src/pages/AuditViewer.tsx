export default function AuditViewer() {
  return (
    <div className="space-y-2">
      <h2 className="font-semibold">Audit viewer</h2>
      <p className="text-sm text-slate-600">
        Audit records are written by the <code>audit_log</code> and <code>infer</code> functions.
        In production, point the audit sink (<code>_lib/audit.ts</code>) at your logging/DB service
        and render its query results here. This page is a placeholder for that integration.
      </p>
    </div>
  );
}
