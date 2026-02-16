import { forwardRef, useImperativeHandle } from 'react';
import { Alert, Dropdown, Flex, Form, Space } from 'antd';
import AppCopyToClipboard from '@unpod/components/third-party/AppCopyToClipboard';
import {
  MdDeleteOutline,
  MdMoreVert,
  MdOutlineCheckCircle,
  MdOutlineContentCopy,
  MdOutlineUnpublished,
} from 'react-icons/md';
import { RiDraftLine } from 'react-icons/ri';
import { deleteDataApi, useInfoViewActionsContext } from '@unpod/providers';
import { AppHeaderButton } from '@unpod/components/common/AppPageHeader';
import { useApp } from '@unpod/custom-hooks';
import { StyledContainer, StyledTitleContainer } from './index.styled';
import BridgeTitle from './BridgeTitle';
import { useMediaQuery } from 'react-responsive';
import AppRegionField from '@unpod/components/common/AppRegionField';
import { DesktopWidthQuery, MobileWidthQuery } from '@unpod/constants';
import { useIntl } from 'react-intl';

type FormatMessage = (descriptor: { id: string }) => string;

const getMenuItems = (
  desktopScreen: boolean,
  sipBridge: any,
  formatMessage: FormatMessage,
) => {
  const menus = [];
  if (desktopScreen) {
    menus.push({
      key: 'draft',
      label: formatMessage({ id: 'bridgeHeader.saveDraft' }),
      icon: (
        <span className="ant-icon">
          <RiDraftLine fontSize={16} />
        </span>
      ),
    });
  }
  if (sipBridge) {
    if (sipBridge.status === 'ACTIVE') {
      menus.push({
        key: 'deactivate',
        label: formatMessage({ id: 'bridgeHeader.deactivate' }),
        icon: (
          <span className="ant-icon">
            <MdOutlineUnpublished fontSize={16} />
          </span>
        ),
      });
    }
    menus.push(
      {
        key: 'copy_slug',
        label: (
          <AppCopyToClipboard
            title={formatMessage({ id: 'bridgeHeader.copyHandle' })}
            text={sipBridge.slug}
            hideIcon={false}
          />
        ),
        icon: (
          <span className="ant-icon">
            <MdOutlineContentCopy fontSize={16} />
          </span>
        ),
      },
      {
        key: 'delete',
        label: (
          <span
            style={{
              color: '#ff4d4f',
            }}
          >
            {formatMessage({ id: 'common.delete' })}
          </span>
        ),
        icon: (
          <span className="ant-icon">
            <MdDeleteOutline fontSize={18} color="#ff4d4f" />
          </span>
        ),
      },
    );
  }
  return menus;
};

type BridgeHeaderProps = {
  loading?: boolean;
  sipBridge?: any;
  selectedNumbers: any[];
  onBridgeDelete: () => void;
  saveBridgeData: (payload: any) => void;
};

const BridgeHeader = forwardRef<any, BridgeHeaderProps>(
  (
    { loading, sipBridge, selectedNumbers, onBridgeDelete, saveBridgeData },
    ref,
  ) => {
    // const [editDescInput, setEditDescInput] = useState(false);
    const infoViewActionsContext = useInfoViewActionsContext();
    const { openConfirmModal } = useApp();
    const form = (ref as any)?.current?.form;
    const { formatMessage } = useIntl();

    const desktopScreen = useMediaQuery(DesktopWidthQuery);
    const mobileScreen = useMediaQuery(MobileWidthQuery);

    useImperativeHandle(ref, () => ({
      onSaveHeaderData: onSaveData,
      form: form,
    }));

    const onSaveData = (
      status = 'ACTIVE',
      callback?: (payload: any, error: any) => void,
    ) => {
      form
        .validateFields()
        .then(() => {
          const payload: any = {
            name: form.getFieldValue('name'),
            description: form.getFieldValue('description') || '',
            status,
            numberIds: selectedNumbers.map(
              (number) => number.number_id || number.id,
            ),
          };
          if (!sipBridge) {
            payload.region = form.getFieldValue('region');
          }
          saveBridgeData(payload);
          // setEditDescInput(false);
          callback?.(payload, null);
        })
        .catch(() => {
          callback?.(null, { error: true });
        });
    };

    const handleDelete = () => {
      deleteDataApi(
        `telephony/bridges/${sipBridge.slug}/`,
        infoViewActionsContext,
      )
        .then((response: any) => {
          infoViewActionsContext.showMessage(response.message);
          onBridgeDelete();
        })
        .catch((error: any) => {
          infoViewActionsContext.showError(error.message);
        });
    };

    const onMenuClick = ({ key }: { key: string }) => {
      if (key === 'deactivate') {
        onSaveData('INACTIVE');
      } else if (key === 'draft') {
        onSaveData('DRAFT');
      } else if (key === 'delete') {
        openConfirmModal({
          content: formatMessage({ id: 'bridgeHeader.deleteBridgeConfirm' }),
          onOk: handleDelete,
        });
      }
    };

    return (
      <StyledContainer>
        <Form
          form={form}
          initialValues={sipBridge}
          onFinish={() => onSaveData(sipBridge?.status)}
        >
          <Flex justify="space-between" gap="12px">
            <StyledTitleContainer>
              <BridgeTitle
                sipBridge={sipBridge}
                onSave={onSaveData}
                onCancel={() => form.setFieldValue('name', sipBridge?.name)}
              />

              {/*{sipBridge && (*/}
              {/*  <Tooltip*/}
              {/*    title={*/}
              {/*      <AppCopyToClipboard*/}
              {/*        title="Copy Handle"*/}
              {/*        text={sipBridge?.slug}*/}
              {/*        hideIcon={false}*/}
              {/*        textColor="white"*/}
              {/*      />*/}
              {/*    }*/}
              {/*  >*/}
              {/*    <StyledAgentInput>*/}
              {/*      <Text type="secondary">*/}
              {/*        {sipBridge?.slug || 'Bridge Handle...'}*/}
              {/*      </Text>*/}
              {/*    </StyledAgentInput>*/}
              {/*  </Tooltip>*/}
              {/*)}*/}

              {sipBridge?.status === 'INACTIVE' && (
                <Alert
                  message={formatMessage({
                    id: 'bridgeHeader.bridgeDeactivated',
                  })}
                  type="warning"
                  showIcon
                />
              )}
            </StyledTitleContainer>

            <Space align="start">
              {!sipBridge && <AppRegionField />}
              {!desktopScreen &&
                (!sipBridge || sipBridge?.status !== 'ACTIVE') && (
                  <AppHeaderButton
                    type="primary"
                    shape="round"
                    size="small"
                    icon={<RiDraftLine fontSize={18} />}
                    onClick={() => onSaveData('DRAFT')}
                    loading={loading}
                    ghost
                  >
                    {formatMessage({ id: 'bridgeHeader.saveDraft' })}
                  </AppHeaderButton>
                )}

              <AppHeaderButton
                type="primary"
                shape="round"
                size="small"
                icon={
                  <MdOutlineCheckCircle fontSize={mobileScreen ? 22 : 18} />
                }
                onClick={() => onSaveData('ACTIVE')}
                loading={loading}
              >
                {mobileScreen
                  ? ''
                  : formatMessage({ id: 'bridgeHeader.publish' })}
              </AppHeaderButton>

              {(sipBridge || desktopScreen) && (
                <Dropdown
                  menu={{
                    items: getMenuItems(
                      desktopScreen,
                      sipBridge,
                      formatMessage,
                    ),
                    onClick: onMenuClick,
                  }}
                  trigger={['click']}
                  placement="bottomRight"
                >
                  <AppHeaderButton
                    shape="circle"
                    size="small"
                    icon={<MdMoreVert fontSize={16} />}
                  />
                </Dropdown>
              )}
            </Space>
          </Flex>
        </Form>
      </StyledContainer>
    );
  },
);

export default BridgeHeader;
