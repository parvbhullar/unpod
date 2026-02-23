import type {Organization} from '../organization';
import type {Spaces} from '../space';
import type {User} from '../user';

export type Thread = {
  post_id?: string | number;
  slug?: string;
  title?: string;
  post_type?: string;
  postType?: string;
  content?: string;
  content_type?: string;
  privacy_type?: string;
  related_post?: Thread[];
  parent_post_slug?: string;
  subPostsLoaded?: boolean;
  knowledge_bases?: Array<{ slug?: string }>;
  related_data?: {
    pilot?: string;
    focus?: string;
    [key: string]: unknown;
  };
  users?: Array<{
    email?: string;
    role?: string;
    [key: string]: unknown;
  }>;
  final_role?: string;
  access_request?: User[];
  request_token?: string | null;
  is_requested?: boolean;
  organization?: Organization;
  space?: Spaces;
  post_status?: string;
  created?: string;
  seen?: boolean;
  loading?: boolean;
  media?: {
    playback_id?: string;
    media_type?: string;
  };
  cover_image?: {
    url?: string;
  };
  block?: {
    data?: {
      content?: string;
      files?: Array<{ file_type?: string; url?: string }>;
    };
  };
  user?: {
    full_name?: string;
    [key: string]: unknown;
  };
  [key: string]: unknown;
};
