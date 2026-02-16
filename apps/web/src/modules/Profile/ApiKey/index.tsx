'use client';
import React, { Fragment, useEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import {
  deleteDataApi,
  postDataApi,
  useAuthContext,
  useGetDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';
import AppTable from '@unpod/components/third-party/AppTable';
import { getApiColumns } from '@/modules/Profile/ApiKey/columns';
import { Button } from 'antd';
import PageBaseHeader from '@unpod/components/common/AppPageLayout/layouts/ThreeColumnPageLayout/PageBaseHeader';
import { MdKey } from 'react-icons/md';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import { ApiKeySkeleton } from '@unpod/skeleton/ApiKey';

const ApiKey = () => {
  const { formatMessage } = useIntl();
  const [isGenerating, setIsGenerating] = useState(false);

  const { activeOrg, isAuthenticated } = useAuthContext();
  const infoViewActionsContext = useInfoViewActionsContext();
  const [{ apiData, loading }, { reCallAPI }] = useGetDataApi<
    Array<{ key?: string; created?: string }>
  >(
    `user/auth-tokens/`,
    { data: [] },
    {
      domain: activeOrg?.domain_handle,
    },
    false,
  );
  useEffect(() => {
    if (isAuthenticated) reCallAPI();
  }, [isAuthenticated, activeOrg]);

  if (!isAuthenticated) {
    return <ApiKeySkeleton />;
  }

  const onGenerateToken = () => {
    setIsGenerating(true);
    postDataApi<unknown>(`user/auth-tokens/`, infoViewActionsContext, {
      domain: activeOrg?.domain_handle,
    })
      .then((res) => {
        setIsGenerating(false);
        infoViewActionsContext.showMessage(res.message || 'Created');
        reCallAPI();
      })
      .catch((error) => {
        const err = error as { message?: string };
        setIsGenerating(false);
        infoViewActionsContext.showError(err.message || 'Error');
      });
  };

  const onDelete = (key: string) => {
    deleteDataApi<unknown>(`user/auth-tokens/${key}/`, infoViewActionsContext, {
      domain: activeOrg?.domain_handle,
    })
      .then((res) => {
        reCallAPI();
        infoViewActionsContext.showMessage(res.message || 'Deleted');
      })
      .catch((error) => {
        const err = error as { message?: string };
        infoViewActionsContext.showError(err.message || 'Error');
      });
  };

  return (
    <Fragment>
      <PageBaseHeader
        pageTitle={formatMessage({ id: 'nav.apiKeys' })}
        titleIcon={<MdKey fontSize={21} />}
        hideToggleBtn
        rightOptions={
          <Button
            type="primary"
            shape="round"
            size="small"
            loading={isGenerating}
            onClick={onGenerateToken}
            disabled={Boolean(apiData?.data?.length)}
          >
            {formatMessage({ id: 'apiKey.generateNew' })}
          </Button>
        }
      />

      <AppPageContainer>
        {loading ? (
          <ApiKeySkeleton />
        ) : (
          <AppTable
            dataSource={apiData?.data}
            columns={getApiColumns(onDelete) as any}
            pagination={false}
            size="middle"
          />
        )}
      </AppPageContainer>
    </Fragment>
  );
};

export default ApiKey;
