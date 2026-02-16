// import AppAgentModule from '@unpod/modules/AppAgentModule';
import { redirect } from 'next/navigation';

export const metadata = {
  title: 'Configure Agent',
};

export default function AiStudioNewPage() {
  // return <AppAgentModule isNew />;
  return redirect('/ai-identity?onboarded=true');
}
