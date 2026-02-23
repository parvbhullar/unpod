import type {Organization} from '../organization';
import type {Spaces} from '../space';
import type {Thread} from '../thread';

export type Conversation = Thread & {
  user?: {
    full_name?: string;
    user_token?: string;
    profile_color?: string;
    profile_picture?: string;
    [key: string]: unknown;
  };
  users?: Array<{
    email?: string;
    full_name?: string;
    role?: string;
    join_date?: string;
    joined?: boolean;
    profile_color?: string;
    profile_picture?: string;
    [key: string]: unknown;
  }>;
  organization?: Organization;
  space?: Spaces;
  [key: string]: unknown;
};
