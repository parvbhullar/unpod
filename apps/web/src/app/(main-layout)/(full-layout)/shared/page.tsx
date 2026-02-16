import SharedWithMe from '../../../../modules/SharedWithMe';

const pageTitle = 'Shared With Me';

export const metadata = {
  title: pageTitle,
};

export default function SharedPage() {
  return <SharedWithMe pageTitle={pageTitle} />;
}
