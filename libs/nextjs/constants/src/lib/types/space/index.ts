import type { Organization } from '../organization';
import type { User } from '../user';

export type Spaces = {
  slug?: string;
  name?: string;
  logo?: string;
  domain_handle?: string;
  organization?: Organization;
  space_type?: string;
  content_type?: string;
  privacy_type?: string;
  description?: string;
  token?: string;
  pilots?: { handle?: string }[];
  space_picture?: string;
  access_request?: User[];
  users?: User[];
  [key: string]: unknown;
};

export type SpaceSchema = {
  type?: string;
  properties?: Record<
    string,
    {
      type?: string;
      title?: string;
      description?: string;
      defaultValue?: string;
    }
  >;
  required?: string[];
  [key: string]: unknown;
};

export type CollectionRecord = {
  id: string;
  name: string;
  source: string;
  content: string;
  total_pages?: number;
  content_hash?: string;
  file_sha1?: string;
  [key: string]: unknown;
};

export type CollectionDataResponse = {
  data: CollectionRecord[];
  schemas?: SpaceSchema;
  count?: number;
  next?: string | null;
  previous?: string | null;
};

export type KnowledgeBase = Spaces & {
  total_post?: number;
  is_owner?: boolean;
  private_main_post_slug?: string | null;
  public_main_post_slug?: string | null;
  last_main_post_slug?: string | null;
  has_evals?: boolean;
  evals_info?: {
    eval_name?: string;
    linked_handle?: string;
    gen_status?: string | undefined;
    eval_token?: string;
  };
};
