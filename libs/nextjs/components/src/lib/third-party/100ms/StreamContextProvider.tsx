'use client';
import React, {createContext, ReactNode, useContext, useEffect, useState} from 'react';
import {isHostUser} from '@unpod/helpers/StreamHelper';
import {getDataApi, useInfoViewActionsContext} from '@unpod/providers';

interface Post {
  slug: string;
  is_live?: boolean;
  post_id?: string;
  roomCode?: string;

  [key: string]: any;
}

interface StreamContextValue {
  role: string | undefined;
  post: Post | null;
  token: string | undefined;
}

interface StreamActionsContextValue {
  // Add action methods here if needed
}

const StreamContext = createContext<StreamContextValue | undefined>(undefined);
const StreamActionsContext = createContext<StreamActionsContextValue | undefined>(undefined);

export const useStreamContext = () => useContext(StreamContext);

export const useStreamActionsContext = () => useContext(StreamActionsContext);

interface StreamContextProviderProps {
  children: ReactNode;
  post: Post;
  token?: string;
}

const StreamContextProvider: React.FC<StreamContextProviderProps> = ({children, post, token}) => {
  const [role, setRole] = useState<string | undefined>();
  const [currentPost, setCurrentPost] = useState<Post | null>(post);
  const infoViewActionsContext = useInfoViewActionsContext();

  // const roomCode = 'vmm-jct-fuc'; // vmm-jct-fuc for sales
  const roomCode = 'tmz-qdi-cyp'; // tmz-qdi-cyp for demo

  // todo set dynamic room code
  const onJoinStream = () => {
    getDataApi(
      `threads/${post.slug}/hms/livesession/token/`,
      infoViewActionsContext
    ).then(({data}) => {
      setCurrentPost({
        ...post,
        roomCode: data?.host_room_code?.code
          ? data?.host_room_code?.code
          : roomCode,
      });
    });
  };

  useEffect(() => {
    if (post) {
      if (post?.is_live) {
        onJoinStream();
      } else if (isHostUser(post)) {
        getDataApi(
          `threads/${post.slug}/hms/livesession/start/`,
          infoViewActionsContext
        ).then(({data}) => {
          setCurrentPost({
            ...post,
            roomCode: data?.host_room_code?.code
              ? data?.host_room_code?.code
              : roomCode,
          });
        });
      } else {
        getDataApi(`threads/${post.slug}/detail/`, infoViewActionsContext).then(
          ({data}) => {
            setCurrentPost(data);
            if (post?.is_live) {
              onJoinStream();
            }
          }
        );
      }
    }
    setRole(isHostUser(post) ? 'host' : 'audience');
  }, [post]);

  return (
    <StreamContext.Provider
      value={{
        role,
        post: currentPost,
        token,
      }}
    >
      <StreamActionsContext.Provider value={{}}>{children}</StreamActionsContext.Provider>
    </StreamContext.Provider>
  );
};

export default StreamContextProvider;
