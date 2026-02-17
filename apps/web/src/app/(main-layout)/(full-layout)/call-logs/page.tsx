import dynamic from 'next/dynamic';

const AuditTable = dynamic<any>(
  () => import('@unpod/modules/AppSIPBridge/AuditTable'),
);

export default function AuditPage() {
  return <AuditTable />;
}
