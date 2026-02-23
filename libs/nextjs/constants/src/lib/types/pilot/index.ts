import type {Organization} from '../organization';
import type {Spaces} from '../space';
import dayjs from 'dayjs';

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
  chat_model?: {
    slug?: string;
    name?: string;
    codename?: string;
    provider_info?: {
      id?: string;
      [key: string]: unknown;
    };
    [key: string]: unknown;
  };
  embedding_model?: { slug?: string; name?: string; codename?: string };
  allow_user_to_change?: boolean;
  users?: InviteMember[];
  organization?: Organization;
  privacy_type?: string;
  created_by?: string | number;
  state?: string;
  access_request?: InviteMember[]; //this is not in agentData
  kb_list?: Spaces[];
  profile?: VoiceProfile;
  voice_profile?: VoiceProfile;
  telephony_config?: TelephonyConfig;
  region?: string;
  components?: {
    Analysis?: AnalysisItem[];
    Integration?: IntegrationItem[];
  };
  calling_time_ranges?: CallingTimeRange[];
  calling_days?: string[];
  handover_number?: string;
  handover_person_name?: string;
  handover_person_role?: string;
  handover_number_cc?: string;
  handover_prompt?: string;
  hub_domain_handle?: string;
  instant_handover?: boolean;
  enable_handover?: boolean;
  notify_via_sms?: boolean;
  number_of_words?: number;
  numbers?: TelephonyNumber[];
  enable_memory?: boolean;
  enable_callback?: boolean;
  enable_followup?: boolean;
  eval_kn_bases?: string[];
  [key: string]: unknown;
};

export type CallingTimeRange = {
  start?: dayjs.Dayjs;
  end?: dayjs.Dayjs;
};

export type VoiceProfileLanguage = {
  code: string;
  name: string;
};

export type ConfigItem = {
  config_key: string;
  config_value: string;
};

export type TelephonyConfig = {
  transcriber?: Transcriber;
  voice?: Voice;
  telephony?: TelephonyNumber[];
  quality?: string;
  config_items?: ConfigItem[];
  voice_profile_id?: string;
};

export type Voice = {
  name?: string;
  provider?: number;
  voice?: string;
  model?: string;
  languages?: VoiceProfileLanguage[];
};

export type Transcriber = {
  name?: string;
  provider?: number;
  model?: string;
  languages?: VoiceProfileLanguage[];
  language?: string;
};

export type TelephonyNumber = {
  id: number;
  number: string;
  provider_details: {
    id: number;
    name: string;
    type: string;
    model_types: string[];
    url: string;
    description: string;
    icon: string;
    status: string;
  };
  country_code: string;
  region: string;
  state: string;
  active: boolean;
  owner_type: string;
  number_type: string;
  association: {
    orgId: string;
    provider: string;
    credentialId: string;
    phone_number_id: string;
  };
  agent_number: boolean;
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
  transcriber?: Transcriber;
  voice?: Voice;
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

export type FormField = {
  id: number;
  title: string;
  placeholder: string | null;
  type: string;
  name: string;
  description: string;
  default: string | null;
  required: boolean;
  regex: string | null;
  config: { [key: string]: string };
  options_type: string | null;
  dependencies: any[];
  options?: {
    title: string;
    description: string;
  }[];
};

export type FormValues = {
  id: number;
  name: string;
  parent_type: string;
  parent_id: string;
  form: number;
  values: any;
};

export type AnalysisItem = {
  id: number;
  name: string;
  slug: string;
  description: string;
  form_fields: FormField[];
  form_values: FormValues;
};

export type IntegrationItem = {
  id: number;
  name: string;
  slug: string;
  description: string;
  form_fields: FormField[];
  form_values: FormValues;
};


export type InviteMember = {
  email?: string;
  role_code?: string;
  invite_by?: string;
  full_name?: string;
  slug?: string;
  [key: string]: unknown;
};


