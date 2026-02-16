import ApiKey from '../../../../modules/Profile/ApiKey';

export const metadata = {
  title: 'User API Keys | Unpod',
  description: 'Manage your Unpod account api keys and preferences.',
};

export default function UserSettingsPage() {
  return <ApiKey />;
}
