import dynamic from 'next/dynamic';

const AuditTable = dynamic<Record<string, unknown>>(
  () => import('@unpod/modules/AppSIPBridge/AuditTable'),
);

export default function AuditPage() {
  return <AuditTable />;
}
