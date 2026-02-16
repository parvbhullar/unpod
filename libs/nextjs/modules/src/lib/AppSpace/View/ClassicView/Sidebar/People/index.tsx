import { useMemo, useState } from 'react';
import SubHeader from './SubHeader';
import AppDocuments from '@unpod/components/modules/AppDocuments';
import {
  useAppSpaceActionsContext,
  useAppSpaceContext,
} from '@unpod/providers';
import { StyledSearchBoxWrapper } from './index.styled';

const People = () => {
  const [search, setSearch] = useState('');
  const [isDocsLoading, setDocsLoading] = useState(false);
  const [filters, setFilters] = useState({});

  const { setSelectedDocs } = useAppSpaceActionsContext();
  const { selectedDocs = [], connectorData } = useAppSpaceContext();

  const records = (connectorData?.apiData || []) as any[];

  const checkedType = useMemo(() => {
    if (selectedDocs?.length === records.length) {
      return 'all';
    } else if (selectedDocs.length === 0) {
      return 'none';
    } else {
      return 'partial';
    }
  }, [selectedDocs, records]);

  /*  useEffect(() => {
    if (currentSpace.token) {
      setFilters();
    }
  }, [currentSpace.token]);*/

  const onToggleCheck = () => {
    if (checkedType === 'none') {
      setSelectedDocs(records.map((doc: any) => doc.document_id));
    } else {
      setSelectedDocs([]);
    }
  };

  return (
    <>
      <StyledSearchBoxWrapper>
        <SubHeader
          onToggleCheck={onToggleCheck}
          checkedType={checkedType}
          isDocsLoading={isDocsLoading}
          setSearch={setSearch}
          filters={filters}
          search={search}
          allowSelection={false}
          setFilters={setFilters}
        />
      </StyledSearchBoxWrapper>
      <AppDocuments
        search={search}
        filters={filters}
        setDocsLoading={setDocsLoading}
      />
    </>
  );
};

export default People;
