export const tablePageSize = 10;
export const AskAttachmentTypes =
  '.png, .jpg, .jpeg, .pdf, .doc, .docx, .txt,  .xls, .xlsx, .csv';

export type PaymentConfigType = {
  RAZORPAY_KEY_ID: string;
  CURRENCY: string;
};

export const PaymentConfig: PaymentConfigType = {
  RAZORPAY_KEY_ID: 'rzp_test_y6dtiSmMIHTUfd',
  // RAZORPAY_KEY_ID: 'rzp_live_I4lHj28SGXjrtT',
  CURRENCY: 'INR',
};

export type MediaQueryConfig = {
  query: string;
};

export const TabWidthQuery: MediaQueryConfig = { query: '(max-width: 768px)' };
export const MobileWidthQuery: MediaQueryConfig = {
  query: '(max-width: 550px)',
};
export const DesktopWidthQuery: MediaQueryConfig = {
  query: '(max-width: 1199px)',
};
export const XssMobileWidthQuery: MediaQueryConfig = {
  query: '(max-width: 360px)',
};
