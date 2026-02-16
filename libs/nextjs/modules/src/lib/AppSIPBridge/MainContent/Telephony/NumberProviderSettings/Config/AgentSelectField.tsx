import { useEffect } from 'react';
import { Select } from 'antd';
import { useAuthContext, usePaginatedDataApi } from '@unpod/providers';
import AppSelect from '@unpod/components/antd/AppSelect';
import { tablePageSize } from '@unpod/constants';

const pageLimit = tablePageSize * 2;

const AgentSelectField = (props: Record<string, any>) => {
  const { activeOrg } = useAuthContext();
  const [{ apiData, loading }, { setQueryParams }] = usePaginatedDataApi(
    `core/pilots/`,
    [],
    {
      page_size: 20,
      domain: activeOrg?.domain_handle,
    },
    false,
  ) as any;

  useEffect(() => {
    if (activeOrg?.domain_handle) {
      setQueryParams({
        domain: activeOrg?.domain_handle,
        page_size: pageLimit,
        page: 1,
      });
    }
  }, [activeOrg]);

  return (
    <AppSelect
      placeholder="Select Agent"
      showSearch={true}
      loading={loading}
      onSearch={(value: string) => {
        setQueryParams({
          domain: activeOrg?.domain_handle,
          search: value,
          page_size: 20,
          page: 1,
        });
      }}
      {...props}
    >
      {(apiData || [])?.map((item: any) => (
        <Select.Option key={item.handle} value={item.handle}>
          {item.name}
        </Select.Option>
      ))}
    </AppSelect>
  );
};

export default AgentSelectField;
