import Summary from './Summary';
import ContentWrapper from '../../components/ContentWrapper';
import {
  useAppSpaceContext,
  useAuthContext,
  useGetDataApi,
} from '@unpod/providers';
import { PeopleOverviewSkeleton } from '@unpod/skeleton/PeopleOverviewSkeleton';

const PeopleOverview = () => {
  const { activeDocument, currentSpace } = useAppSpaceContext();
  const { activeOrg } = useAuthContext();

  const [{ apiData, loading }] = useGetDataApi(
    `knowledge_base/${currentSpace?.token}/connector-doc-data/${activeDocument?.document_id}/`,
    { data: {} },
    {
      domain: activeOrg?.domain_handle,
      page_size: 20,
      page: 1,
    },
  ) as unknown as [{ apiData?: { data?: unknown }; loading: boolean }];

  if (loading) {
    return <PeopleOverviewSkeleton />;
  }
  return (
    <ContentWrapper>
      <Summary data={apiData?.data ?? null} />
    </ContentWrapper>
  );
};

export default PeopleOverview;
