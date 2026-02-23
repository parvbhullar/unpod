import type {Organization} from '../organization';
import type {Spaces} from '../space';

export type User = {
  id?: string | number;
  domain?: string;
  domain_handle?: string;
  is_private_domain?: boolean;
  first_name?: string;
  phone_number?: string;
  last_name?: string;
  email?: string;
  verify_email?: boolean;
  full_name?: string;
  user_detail?: {
    role_name?: string | null;
    description?: string | null;
    profile_color?: string | null;
    profile_picture?: string | null;
    preferred_language?: string | null;
  };
  organization?: Organization;
  active_organization?: Organization;
  organization_list?: Organization[];
  active_space?: Spaces;
  space?: Array<{ role?: string; token?: string; name?: string }>;
  space_invitation?: Array<{
    name?: string;
    role?: string;
    invite_by?: string;
    invite_token?: string;
    invite_verified?: boolean;
    valid_upto?: string;
    user_email?: string;
    joined?: boolean;
    invite_type?: string;
    [key: string]: unknown;
  }>;
  user_token?: string;
  current_step?: string;
  [key: string]: unknown;
};
