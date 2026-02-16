export const PENDING_UPLOAD_STATUS = 'pending';

export const DOCUMENT_STATUS = {
  [PENDING_UPLOAD_STATUS]: { color: 'badge-warning', label: 'common.pending' },
  review: { color: 'badge-info', label: 'common.inReview' },
  reject: { color: 'badge-error', label: 'callLogs.rejected' },
  verify: { color: 'badge-success', label: 'common.verified' },
  approve: { color: 'badge-success', label: 'common.approved' },
};

export const requiredDocs = [
  {
    document_type: 'GST_CERTIFICATE',
    label: 'bridge.gstCertificate',
    key: 'gst_certificate',
    status: PENDING_UPLOAD_STATUS,
  },
  {
    document_type: 'COMPANY_PAN',
    label: 'bridge.companyPan',
    key: 'company_pan',
    status: PENDING_UPLOAD_STATUS,
  },
  {
    document_type: 'INCORPORATION_CERTIFICATE',
    label: 'bridge.incorporationCertificate',
    key: 'incorporation_certificate',
    status: PENDING_UPLOAD_STATUS,
  },
  {
    document_type: 'AADHAR_CARD',
    label: 'bridge.aadhaarCard',
    key: 'aadhar_card',
    status: PENDING_UPLOAD_STATUS,
  },
];
