import type { Organization } from '../organization';
import type { User } from '../user';
import type { Spaces } from '../space';

export type Pilot = {
  slug?: string;
  handle?: string;
  name?: string;
  description?: string;
  type?: string;
  tags?: string[];
  logo?: string;
  ai_persona?: string;
  response_prompt?: string;
  questions?: string[];
  knowledge_bases?: Array<string | Spaces>;
  plugins?: string[];
  config?: {
    voice?: Record<string, string>;
    chat?: Record<string, unknown>;
    embedding?: Record<string, unknown>;
  };
  chat_model?: { slug?: string; name?: string; codename?: string };
  embedding_model?: { slug?: string; name?: string; codename?: string };
  allow_user_to_change?: boolean;
  users?: User[];
  user_list?: Array<{ role_code?: string; [key: string]: unknown }>;
  organization?: Organization;
  privacy_type?: string;
  created_by?: string | number;
  state?: string;
  access_request?: User[];
  kb_list?: Spaces[];
  profile?: VoiceProfile;
  voice_profile?: VoiceProfile;
  telephony_config?: Record<string, unknown>;
  [key: string]: unknown;
};

export type VoiceProfileLanguage = {
  code: string;
  name: string;
};

export type VoiceProfile = {
  agent_profile_id?: string;
  name?: string;
  quality?: string;
  gender?: string;
  temperature?: number;
  voice_temperature?: number;
  voice_speed?: number;
  greeting_message?: string;
  description?: string;
  voice_prompt?: string;
  estimated_cost?: string;
  latency?: string;
  chat_model?: {
    name?: string;
    slug?: string;
    codename?: string;
    provider?: number;
  };
  transcriber?: {
    name?: string;
    provider?: number;
    model?: string;
    languages?: VoiceProfileLanguage[];
  };
  voice?: {
    name?: string;
    provider?: number;
    voice?: string;
    model?: string;
    languages?: VoiceProfileLanguage[];
  };
  [key: string]: unknown;
};

export type ProviderModelLanguage = {
  id: number;
  name: string;
  code: string;
};

export type ProviderModelVoice = {
  id?: number;
  name?: string;
  code?: string;
  [key: string]: unknown;
};

export type ProviderInfo = {
  id: number;
  name: string;
  type: string;
  model_types: string[];
  url: string | null;
  description: string;
  icon: string | null;
  status: string;
};

export type ProviderModel = {
  id: number;
  name: string;
  slug: string;
  codename: string;
  logo: string | null;
  description: string;
  token_limit: number | null;
  provider: number;
  provider_info: ProviderInfo;
  tags: string[];
  config: Record<string, unknown>;
  languages: ProviderModelLanguage[];
  voices: ProviderModelVoice[];
  realtime_sts: boolean;
  inference: boolean;
  status: string;
};
