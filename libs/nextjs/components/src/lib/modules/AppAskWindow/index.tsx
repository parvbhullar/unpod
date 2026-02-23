import React, {useCallback, useEffect, useMemo, useState} from 'react';
import PropTypes from 'prop-types';
import {
  getDataApi,
  postDataApi,
  uploadDataApi,
  useAuthContext,
  useGetDataApi,
  useInfoViewActionsContext,
  useOrgContext,
} from '@unpod/providers';
import {useParams, useRouter} from 'next/navigation';
import _debounce from 'lodash/debounce';
import {getDraftData, saveDraftData} from '@unpod/helpers/DraftHelper';
import {AskAttachmentTypes, PERMISSION_TYPES} from '@unpod/constants';
import {ACCESS_ROLE, POST_CONTENT_TYPE, POST_TYPE,} from '@unpod/constants/AppEnums';
import {
  StyledBottomBar,
  StyledCloseButton,
  StyledContainer,
  StyledEscapeText,
  StyledIconWrapper,
  StyledInput,
  StyledOverlay,
  StyledRoot,
  StyledSelect,
  StyledTopBar,
  StylesPilotLogo,
} from './index.styled';
import clsx from 'clsx';
import {Badge, Button, Col, Dropdown, Form, Row, Select, Space, Typography, Upload,} from 'antd';
import PostPermissionPopover from '../../common/PermissionPopover/PostPermissionPopover';
import {MdArrowForward, MdClose, MdDelete, MdOutlineAttachment, MdOutlineWorkspaces,} from 'react-icons/md';
import {getFileExtension} from '@unpod/helpers/FileHelper';
import {BsFillFileEarmarkPersonFill} from 'react-icons/bs';
import AppLoader from '../../common/AppLoader';
import AppImage from '../../next/AppImage';
import AppSuperbookInputs from '../../common/AppSuperbookInputBlock/AppSuperbookInputs';
import {getDateObject} from '@unpod/helpers/DateHelper';
import {getJsonString} from '@unpod/helpers/StringHelper';
import {getLocalizedOptions} from '@unpod/helpers/LocalizationFormatHelper';
import {useIntl} from 'react-intl';

const defaultPilot = {
  handle: 'superpilot',
  name: '@Superpilot',
};

const {Item, useForm} = Form;

const AppAskWindow = ({
                        position,
                        isStatic,
                        onQuestionSaved,
                        reloadPostApi,
                        pilotHandle,
                        currentHubSlug,
                        onSaved,
                        hideCloseInfo,
                      }) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const {isAuthenticated, user} = useAuthContext();
  const {activeSpace} = useOrgContext();
  const router = useRouter();
  const {spaceSlug, postSlug} = useParams();
  const [form] = useForm();
  const {formatMessage} = useIntl();

  const [focused, setFocused] = React.useState(isStatic || false);
  const [queryTitle, setQueryTitle] = React.useState(null);
  const [showDesc, setShowDesc] = React.useState(false);
  const [queryDescription, setQueryDescription] = React.useState(null);
  const [privacyType, setPrivacyType] = useState('public');
  const [currentPrivacy, setCurrentPrivacy] = useState(null);
  const [spaceList, setSpaceList] = useState([]);
  const [selectedSpace, setSelectedSpace] = useState(null);
  const [open, setOpen] = useState(false);
  const [userList, setUserList] = useState([]);
  const [dataFetched, setDataFetched] = useState(false);
  const [requestPilot, setRequestedPilot] = useState(defaultPilot.handle);
  const [pilot, setPilot] = useState(defaultPilot);
  const [kbList, setKbList] = useState([]);
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [attachments, setAttachments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [inputFormBlock, setInputFormBlock] = useState(null);

  const debounceFn = useCallback(_debounce(saveDraftData, 2000), []);

  const [{apiData: pilots}] = useGetDataApi(
    `core/pilots/public/`,
    {},
    {
      case: 'all',
    },
  );

  const [{apiData: knBasesData}] = useGetDataApi(
    `core/knowledgebase/`,
    {},
    {
      domain: currentHubSlug,
    },
  );

  useEffect(() => {
    const routeChangeStart = () => {
      setDataFetched(false);
    };

    router.events.on('routeChangeStart', routeChangeStart);

    return () => {
      router.events.off('routeChangeStart', routeChangeStart);
    };
  }, []);

  useEffect(() => {
    if (dataFetched) {
      debounceFn(postSlug || spaceSlug, {
        title: queryTitle,
        description: queryDescription,
        privacy: privacyType,
        users: userList,
      });
    }
  }, [
    queryTitle,
    queryDescription,
    privacyType,
    userList,
    spaceSlug,
    postSlug,
    dataFetched,
  ]);

  useEffect(() => {
    if (!dataFetched) {
      const draftData = getDraftData(postSlug || spaceSlug);

      if (draftData) {
        setQueryTitle(draftData.title);
        setQueryDescription(draftData.description);
        setPrivacyType(draftData.privacy);
        setUserList(draftData.users);
      }

      setTimeout(() => {
        setDataFetched(true);
      }, 1000);
    }
  }, [spaceSlug, postSlug, dataFetched]);

  useEffect(() => {
    if (user) {
      if (user.space) {
        const spaces = [];

        user.space.forEach((item) => {
          if (item.role !== 'viewer') {
            spaces.push({
              key: item.token,
              label: item.name,
              token: item.token,
            });
          }
        });
        setSpaceList(spaces);

        if (user.active_space) {
          setSelectedSpace(
            spaces.find((space) => space.token === user.active_space.token),
          );
        }
      }
    }
  }, [user]);

  useEffect(() => {
    if (!pilotHandle) {
      if (activeSpace) {
        if (activeSpace?.users) {
          setUserList(
            activeSpace?.users.map((item) => ({
              ...item,
              role_code: item.role,
            })),
          );
        } else {
          setUserList([]);
        }

        if (activeSpace.privacy_type) {
          const privacy = PERMISSION_TYPES.find(
            (item) => item.key === activeSpace.privacy_type,
          );
          setPrivacyType(privacy.key);
        }
      }
    }
  }, [activeSpace, pilotHandle]);

  useEffect(() => {
    if (pilotHandle) setRequestedPilot(pilotHandle);
  }, [pilotHandle]);

  useEffect(() => {
    if (requestPilot) {
      const pilot = pilots?.data?.find((item) => item.handle === requestPilot);

      if (pilot) {
        if (pilot.allow_user_to_change) {
          setKbList(pilot.kb_list || []);
        } else {
          setKbList([]);
        }
      } else {
        setKbList(knBasesData?.data);
      }

      if (requestPilot !== defaultPilot.handle) {
        getDataApi(
          `core/pilots/${requestPilot}/blocks/`,
          infoViewActionsContext,
        )
          .then((response) => {
            setLoading(false);

            setInputFormBlock(
              response.data.find(
                (block) => block.block_type === 'input_form',
              ) || null,
            );
          })
          .catch((error) => {
            setLoading(false);
            if (error.message !== 'Pilot Not Found') {
              infoViewActionsContext.showError(error.message);
            }
          });
      } else {
        setInputFormBlock(null);
      }
    }
  }, [requestPilot, pilots?.data, knBasesData?.data]);

  useEffect(() => {
    if (inputFormBlock?.input_schema) {
      const initialData = {};
      for (const item of inputFormBlock.input_schema) {
        if (item.type === 'date') {
          initialData[item.name] = item.defaultValue
            ? getDateObject(item.defaultValue, 'YYYY-MM-DD')
            : null;
        } else if (item.type === 'time') {
          initialData[item.name] = item.defaultValue
            ? getDateObject(item.defaultValue, 'HH:mm:ss')
            : null;
        } else if (item.type === 'datetime') {
          initialData[item.name] = item.defaultValue
            ? getDateObject(item.defaultValue, 'YYYY-MM-DD HH:mm:ss')
            : null;
        } else if (item.type === 'json') {
          initialData[item.name] = item.defaultValue
            ? getJsonString(item.defaultValue)
            : null;
        } else {
          initialData[item.name] = item.defaultValue || null;
        }
      }

      form.setFieldsValue(initialData);
    }
  }, [inputFormBlock?.input_schema]);

  useEffect(() => {
    setCurrentPrivacy(
      PERMISSION_TYPES.find((item) => item.key === privacyType),
    );
  }, [privacyType]);

  const resetForm = () => {
    setQueryTitle(null);
    setQueryDescription(null);
    setPrivacyType('public');
    setUserList([]);
  };

  const uploadAttachments = (callbackFun, payload) => {
    const formData = new FormData();
    formData.append('object_type', 'post');
    attachments.forEach((file) => {
      formData.append('files', file);
    });

    uploadDataApi(`media/upload-multiple/`, infoViewActionsContext, formData)
      .then((res) => {
        payload.files = res.data;
        setAttachments([]);
        callbackFun(payload);
      })
      .catch((response) => {
        infoViewActionsContext.showError(response.message);
      });
  };

  const savePost = (payload) => {
    const requestUrl = `threads/${selectedSpace?.token}/`;

    postDataApi(requestUrl, infoViewActionsContext, payload)
      .then((res) => {
        localStorage.removeItem(postSlug || spaceSlug);
        resetForm();
        if (onQuestionSaved) onQuestionSaved(res.data);
        if (reloadPostApi) reloadPostApi();
        if (onSaved) onSaved();

        infoViewActionsContext.showMessage(res.message);
        setLoading(false);

        router.push(
          `/${res.data.organization.domain_handle}/${res.data.space.slug}/${res.data.slug}/`,
        );
      })
      .catch((error) => {
        infoViewActionsContext.showError(error.message);
        setLoading(false);
      });
  };

  const onQuerySubmit = (values) => {
    if (values || attachments?.length) {
      if (selectedSpace?.token) {
        setLoading(true);

        const payload = {
          // title: queryTitle,
          content:
            Object.keys(values).length > 0 ? JSON.stringify(values) : null,
          post_type: POST_TYPE.ASK,
          content_type: POST_CONTENT_TYPE.TEXT,
          privacy_type: privacyType,
          pilot: requestPilot,
          knowledge_bases: knowledgeBases,
          user_list:
            privacyType === 'shared'
              ? userList.filter((user) => user.role_code !== ACCESS_ROLE.OWNER)
              : [],
          tags: [],
        };

        if (attachments?.length) {
          uploadAttachments(savePost, payload);
        } else {
          savePost(payload);
        }
      } else {
        infoViewActionsContext.showError(
          formatMessage({id: 'validation.selectSpace'}),
        );
      }
    }
  };

  const onSpaceChange = (option) => {
    setSelectedSpace(spaceList.find((space) => space.key === option.key));
  };

  const onShareChange = (option) => {
    setPrivacyType(option.key);

    if (option.key === 'shared') {
      setOpen(true);
    }
  };

  const onFocused = () => {
    setFocused(true);
  };

  const onBlurred = () => {
    setFocused(false);
  };

  const onChangePilot = (newPilot) => {
    setKnowledgeBases([]);
    setRequestedPilot(newPilot);
    setPilot(pilots?.data?.find((item) => item.handle === newPilot));
  };

  const onClosePilot = () => {
    setPilot(null);
    setKnowledgeBases([]);
    setRequestedPilot(null);
    setInputFormBlock(null);
  };

  const handleAttachmentChange = (file) => {
    const extension = getFileExtension(file.name)?.toLowerCase();
    if (
      AskAttachmentTypes &&
      !AskAttachmentTypes.includes(extension) &&
      (!file.type ||
        (!AskAttachmentTypes.includes(file.type) &&
          !AskAttachmentTypes.split('/').includes(file.type?.split('/')[0])))
    ) {
      infoViewActionsContext.showError(
        formatMessage({id: 'validation.fileTypeNotAllowed'}),
      );
    } else {
      setAttachments((prevState) => [...prevState, file]);
    }

    return false;
  };

  const onAttachmentRemove = (event, file) => {
    event.stopPropagation();
    setAttachments((prevState) =>
      prevState.filter((item) => item.uid !== file.uid),
    );
  };

  const attachmentsList = useMemo(() => {
    return attachments.map((item) => ({
      key: item.uid,
      label: (
        <Row justify="space-between" align="middle">
          <Typography.Text style={{marginRight: 5}}>
            {item.name}
          </Typography.Text>
          <MdDelete
            fontSize={18}
            onClick={(event) => onAttachmentRemove(event, item)}
          />
        </Row>
      ),
    }));
  }, [attachments]);

  return (
    <React.Fragment>
      <Form onFinish={onQuerySubmit} form={form}>
        <StyledRoot
          className={clsx({sticky: position === 'sticky'})}
          onFocus={onFocused}
          onMouseDown={onFocused}
          style={{position}}
        >
          <StyledTopBar>
            <Space size="small" align="center">
              {pilot?.logo ? (
                <StylesPilotLogo>
                  <AppImage
                    src={`${pilot.logo}?tr=w-100,h-100`}
                    alt="logo"
                    height={100}
                    width={100}
                    layout="fill"
                    objectFit="cover"
                  />
                </StylesPilotLogo>
              ) : (
                <StyledIconWrapper>
                  <BsFillFileEarmarkPersonFill fontSize={18}/>
                </StyledIconWrapper>
              )}

              <StyledSelect
                placeholder="Select Pilot"
                variant="borderless"
                size="small"
                value={requestPilot}
                onChange={onChangePilot}
                style={{
                  minWidth: 120,
                  width: 'max-content',
                }}
              >
                <Select.Option value="superpilot">@SuperPilot</Select.Option>

                {pilots?.data?.map((item) => (
                  <Select.Option key={item.slug} value={item.handle}>
                    {item.name}
                  </Select.Option>
                ))}
              </StyledSelect>

              {requestPilot && (
                <StyledCloseButton onClick={onClosePilot}>
                  <MdClose/>
                </StyledCloseButton>
              )}
            </Space>

            {requestPilot === 'superpilot' && isAuthenticated && (
              <Space size="small" align="center">
                <MdOutlineWorkspaces fontSize={20}/>

                <Select
                  variant="borderless"
                  size="small"
                  style={{
                    minWidth: 160,
                    width: 'max-content',
                  }}
                  mode="multiple"
                  maxTagCount={1}
                  placeholder={formatMessage({id: 'knowledgeBase.pageTitle'})}
                  disabled={kbList?.length === 0}
                  value={knowledgeBases}
                  onChange={setKnowledgeBases}
                >
                  {kbList?.map((item) => (
                    <Select.Option key={item.slug} value={item.slug}>
                      {item.name}
                    </Select.Option>
                  ))}
                </Select>
              </Space>
            )}
          </StyledTopBar>

          <StyledContainer
            className={clsx({active: showDesc, focused: focused})}
          >
            {inputFormBlock && (
              <Row gutter={16}>
                {(inputFormBlock?.input_schema || []).map((item, index) =>
                  item.type === 'checkboxes' ? (
                    <Col key={index} xs={24} sm={24} md={24}>
                      <AppSuperbookInputs item={item}/>
                    </Col>
                  ) : item.type === 'textarea' || item.type === 'json' ? (
                    <Col key={index} xs={24} sm={24} md={24}>
                      <AppSuperbookInputs item={item}/>
                    </Col>
                  ) : (
                    <Col key={index} xs={24} sm={12} md={8}>
                      <AppSuperbookInputs item={item}/>
                    </Col>
                  ),
                )}
              </Row>
            )}

            <Item name="content">
              <StyledInput
                placeholder={
                  (inputFormBlock?.input_schema || []).length > 0
                    ? formatMessage({id: 'superbook.instructionsOptional'})
                    : formatMessage({id: 'superbook.askMeAnything'})
                }
                maxLength={200}
                variant="borderless"
                autoSize={{minRows: 2, maxRows: 3}}
                size="large"
              />
            </Item>
          </StyledContainer>

          <StyledBottomBar>
            {isAuthenticated ? (
              <Space size="small" align="center" wrap>
                <Dropdown
                  menu={{
                    items: spaceList,
                    onClick: onSpaceChange,
                    selectedKeys: selectedSpace?.key,
                    style: {maxHeight: 220, overflowY: 'auto'},
                  }}
                  trigger={['click']}
                  arrow
                >
                  <Button type="default" size="small">
                    <Space align="center">
                      <MdOutlineWorkspaces fontSize={21}/>

                      <span>
                        {selectedSpace?.label
                          ? selectedSpace.label.slice(0, 20).trim()
                          : formatMessage({id: 'space.space'})}
                      </span>
                    </Space>
                  </Button>
                </Dropdown>

                <PostPermissionPopover
                  open={open}
                  setOpen={setOpen}
                  userList={userList}
                  setUserList={setUserList}
                  placement="top"
                >
                  <Dropdown
                    menu={{
                      items: getLocalizedOptions(
                        PERMISSION_TYPES,
                        formatMessage,
                      ),
                      onClick: onShareChange,
                      selectedKeys: currentPrivacy?.key,
                    }}
                    trigger={['click']}
                    disabled={open}
                    arrow
                  >
                    <Button type="default" size="small">
                      <Space align="center">
                        {currentPrivacy?.icon}
                        <span>
                          {formatMessage({id: currentPrivacy?.label})}
                        </span>
                      </Space>
                    </Button>
                  </Dropdown>
                </PostPermissionPopover>
              </Space>
            ) : (
              <div/>
            )}

            <Space align="center">
              {/*<Button
              type="default"
              shape="circle"
              size="small"
              icon={
                <MdArrowForwardIos
                  fontSize={18}
                  style={{
                    rotate: showDesc ? '270deg' : '90deg',
                    transition: 'rotate 0.2s ease-in',
                  }}
                />
              }
              onClick={() => setShowDesc(!showDesc)}
            />*/}

              <Upload
                name="files"
                accept={AskAttachmentTypes}
                maxCount={10}
                beforeUpload={handleAttachmentChange}
                showUploadList={false}
                multiple
              >
                {attachments?.length > 0 ? (
                  <Dropdown
                    menu={{
                      items: attachmentsList,
                    }}
                    trigger={['hover']}
                    placement="top"
                    arrow
                  >
                    <Badge
                      count={attachments?.length}
                      size="small"
                      offset={[-5, 2]}
                    >
                      <Button
                        type={attachments?.length ? 'primary' : 'default'}
                        shape="circle"
                        icon={<MdOutlineAttachment fontSize={18}/>}
                      />
                    </Badge>
                  </Dropdown>
                ) : (
                  <Button
                    type={attachments?.length ? 'primary' : 'default'}
                    shape="circle"
                    icon={<MdOutlineAttachment fontSize={18}/>}
                  />
                )}
              </Upload>

              <Button type="primary" shape="round" htmlType="submit">
                <Space>
                  {formatMessage({id: 'common.run'})}{' '}
                  <MdArrowForward fontSize={18}/>
                </Space>
              </Button>

              {/*<Button
                type={isEnabled ? 'primary' : 'default'}
                shape="circle"
                size="small"
                icon={<MdArrowForward fontSize={18} />}
                onClick={onQuerySubmit}
              />*/}
            </Space>
          </StyledBottomBar>

          {!hideCloseInfo && (
            <StyledEscapeText type="secondary">
              {formatMessage({id: 'common.esc'})}
            </StyledEscapeText>
          )}
        </StyledRoot>
      </Form>

      {!isStatic && (
        <StyledOverlay
          onClick={onBlurred}
          className={clsx({focused: focused})}
        />
      )}

      {loading && <AppLoader/>}
    </React.Fragment>
  );
};

AppAskWindow.propTypes = {
  position: PropTypes.string,
  isStatic: PropTypes.bool,
  onQuestionSaved: PropTypes.func,
  toolbarId: PropTypes.string,
  pilotHandle: PropTypes.string,
  currentHubSlug: PropTypes.string,
  onSaved: PropTypes.func,
  hideCloseInfo: PropTypes.bool,
};

AppAskWindow.defaultProps = {
  position: 'sticky',
  isStatic: false,
  hideCloseInfo: false,
};

export default AppAskWindow;
