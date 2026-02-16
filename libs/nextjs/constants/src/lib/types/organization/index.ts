import type { User } from '../user';

export type Organization = {
  domain_handle?: string;
  logo?: string;
  account_type?: string[];
  name?: string;
  privacy_type?: string;
  region?: string;
  color?: string;
  is_private_domain?: boolean;
  access_request?: User[];
  users?: User[];
  seeking?: string[];
  tags?: string[];
  org_id?: number;
  pilot_handle?: string | null;
  created?: string;
  modified?: string;
  token?: string;
  domain?: string;
  description?: string | null;
  org_type?: string;
  status?: string;
  telephony_number?: string | null;
  pilot?: number | null;
  [key: string]: unknown;
};
