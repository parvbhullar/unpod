'use client';
import { Fragment, useEffect, useRef } from 'react';
import {
  useAppSpaceActionsContext,
  useAppSpaceContext,
  useAuthContext,
} from '@unpod/providers';
import { generateKbSchema } from '@unpod/helpers/AppKbHelper';
import { CONTACT_SPACE_FIELDS } from '@unpod/constants';
import GuestView from './GuestView';
import PublicView from './PublicView';
import CommonView from './CommonView';
import ClassicView from './ClassicView';
import RequestView from './RequestView';

const SpaceModule = ({ tab, id }: { tab: any; id: any }) => {
  const { currentSpace } = useAppSpaceContext();
  const { setSpaceSchema, setActiveTab, setPathData } =
    useAppSpaceActionsContext();
  const { isAuthenticated, isLoading } = useAuthContext();
  const queryRef = useRef(null);

  useEffect(() => {
    setActiveTab(tab);
    setPathData({ tab, id });
  }, [tab]);

  useEffect(() => {
    if (currentSpace) {
      if (currentSpace?.content_type === 'contact') {
        setSpaceSchema(
          (currentSpace?.schema ||
            generateKbSchema(CONTACT_SPACE_FIELDS)) as any,
        );
      }
    }
  }, [currentSpace]);

  const onDataSaved = (data: any) => {
    console.log('onDataSaved data', data);
    // setActiveConversation(data);
    // reCallAPI();
    // if (queryRef?.current) {
    //   queryRef.current.resetInput();
    // }
  };
  // console.log('Space Data', currentSpace);
  return (
    <Fragment>
      {(currentSpace?.privacy_type === 'shared' &&
        (currentSpace?.final_role === 'guest' ||
          currentSpace?.final_role === 'viewer')) ||
      (currentSpace?.privacy_type === 'public' &&
        (currentSpace?.final_role === 'guest' ||
          currentSpace?.final_role === 'viewer')) ? (
        <RequestView />
      ) : (
        !isLoading &&
        (currentSpace?.token ? (
          <Fragment>
            {isAuthenticated ? (
              currentSpace?.content_type === 'general' ||
              currentSpace?.content_type === 'email' ||
              currentSpace?.content_type === 'contact' ? (
                <ClassicView />
              ) : (
                <CommonView onDataSaved={onDataSaved} queryRef={queryRef} />
              )
            ) : (
              <PublicView queryRef={queryRef} onDataSaved={onDataSaved} />
            )}
          </Fragment>
        ) : (
          <GuestView />
        ))
      )}
    </Fragment>
  );
};

export default SpaceModule;
