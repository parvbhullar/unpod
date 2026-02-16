import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useParams, usePathname, useRouter } from 'next/navigation';
import {
  getDataApi,
  useAuthContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import {
  MdArticle,
  MdAudiotrack,
  MdQuestionAnswer,
  MdTask,
  MdVideoLibrary,
} from 'react-icons/md';
import {
  StyledIconWrapper,
  StyledMenuItem,
  StyledSubMenuItem,
  StyledSubMenuText,
} from './index.styled';
import { Tooltip } from 'antd';
import { RiEditLine } from 'react-icons/ri';
import PageSidebar from '@unpod/components/common/AppPageLayout/layouts/ThreeColumnPageLayout/PageSidebar';
import type { ApiResponse } from '@/types/common';
import type { Thread } from '@unpod/constants/types';

const ICONS = {
  post_text: <MdArticle fontSize={16} />,
  post_video: <MdVideoLibrary fontSize={16} />,
  post_audio: <MdAudiotrack fontSize={16} />,
  post_video_stream: <MdVideoLibrary fontSize={16} />,
  post_audio_stream: <MdAudiotrack fontSize={16} />,
  article_text: <MdArticle fontSize={16} />,
  article_video: <MdVideoLibrary fontSize={16} />,
  article_audio: <MdAudiotrack fontSize={16} />,
  article_video_stream: <MdVideoLibrary fontSize={16} />,
  article_audio_stream: <MdAudiotrack fontSize={16} />,
  task_text: <MdTask fontSize={16} />,
  ask_text: <MdTask fontSize={16} />,
  question_text: <MdQuestionAnswer fontSize={16} />,
};

type MenuOptions = {
  key?: string;
  icon?: React.ReactNode;
  path?: string;
  children?: unknown[];
  title?: string;
  isEdit?: boolean;
  onTitleClick?: () => void;
};

const getRootPostMenuItem = (options: MenuOptions) => {
  const { key, icon, path, children, title, isEdit, onTitleClick } = options;

  const keyString = path ? (isEdit ? `${path}/edit/` : path) : key;

  return {
    key: keyString,
    icon,
    children,
    label: (
      <StyledMenuItem onClick={onTitleClick}>
        <Tooltip title={isEdit ? `Draft - ${title}` : title} placement="right">
          {title}
        </Tooltip>
      </StyledMenuItem>
    ),
  };
};

const getPostMenuItem = (options: MenuOptions) => {
  const { key, icon, path, children, title, isEdit } = options;

  const keyString = path ? (isEdit ? `${path}/edit/` : path) : key;

  return {
    key: keyString,
    children,
    label: (
      <StyledSubMenuItem>
        {isEdit ? (
          <StyledIconWrapper>
            <RiEditLine fontSize={16} />
          </StyledIconWrapper>
        ) : (
          icon
        )}
        <Tooltip title={isEdit ? `Draft - ${title}` : title} placement="right">
          <StyledSubMenuText>{title}</StyledSubMenuText>
        </Tooltip>
      </StyledSubMenuItem>
    ),
    title: isEdit && title ? `Draft - ${title}` : title,
  };
};

type ThreadPost = Thread & { related_post: Thread[] };

type ThreadMenusProps = {
  currentPost?: ThreadPost | null;
};

type IconKey = keyof typeof ICONS;

const ThreadMenus = ({ currentPost }: ThreadMenusProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { isAuthenticated } = useAuthContext();
  const router = useRouter();
  const pathname = usePathname();
  const { orgSlug, spaceSlug, postSlug } = useParams();
  const currentRoute = useRef(pathname);

  const [posts, setPosts] = useState<ThreadPost[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (currentPost?.space?.token) {
      getDataApi(
        `threads/${currentPost?.space?.token}/`,
        infoViewActionsContext,
        {
          layout: 'sidebar',
          page_size: 50,
        },
      )
        .then((response) => {
          const res = response as ApiResponse<ThreadPost[]>;
          setPosts(res.data || []);
          setLoading(false);
        })
        .catch((error) => {
          console.log('error', error);
          setLoading(false);
        });
    }
  }, [currentPost?.space?.token]);

  useEffect(() => {
    if (currentPost?.slug) {
      const rootPost = currentPost?.parent_post_slug
        ? posts?.find((item) => item.slug === currentPost.parent_post_slug)
        : currentPost;

      if (rootPost && rootPost?.related_post?.length > 0) {
        if (!rootPost?.subPostsLoaded) {
          getDataApi(`threads/${rootPost.slug}/post/`, infoViewActionsContext, {
            page_size: 50,
          })
            .then((res) => {
              const response = res as ApiResponse<Thread[]>;
              setPosts((prevState) => {
                return prevState.map((item) => {
                  if (rootPost.slug === item.slug) {
                    item.related_post = response.data || [];
                    item.subPostsLoaded = true;
                  }

                  return item;
                });
              });
            })
            .catch((error) => {
              infoViewActionsContext.showError(error.message);
            });
        }
      }
    }
  }, [currentPost?.slug, posts]);

  const onRootPostTitleClick = (path: string) => {
    if (currentRoute.current !== path) router.push(path);
  };

  const getMenus = useMemo(() => {
    return posts.map((post) => {
      if ((post.related_post || []).length > 0) {
        const rootPostPath = `/${post?.organization?.domain_handle}/${post.space?.slug}/${post.slug}/`;
        const rootIconKey =
          `${post.post_type ?? 'post'}_${post.content_type ?? 'text'}` as IconKey;

        return getRootPostMenuItem({
          title: post.title,
          icon: (
            <StyledIconWrapper>
              {ICONS[rootIconKey] || <MdArticle fontSize={16} />}
            </StyledIconWrapper>
          ),
          key: post.slug,
          path: rootPostPath,
          onTitleClick: () => onRootPostTitleClick(rootPostPath),
          children: [
            ...post.related_post.map((subPost) => {
              const subIconKey =
                `${subPost.post_type ?? 'post'}_${subPost.content_type ?? 'text'}` as IconKey;
              return getPostMenuItem({
                title: subPost.title,
                icon: (
                  <StyledIconWrapper>
                    {ICONS[subIconKey] || <MdArticle fontSize={16} />}
                  </StyledIconWrapper>
                ),
                key: subPost.slug,
                path: `/${post?.organization?.domain_handle}/${post.space?.slug}/${subPost.slug}/`,
                isEdit: subPost.post_status === 'draft',
              });
            }),
          ],
        });
      }

      const postIconKey =
        `${post.post_type ?? 'post'}_${post.content_type ?? 'text'}` as IconKey;
      return getPostMenuItem({
        title: post.title,
        icon: (
          <StyledIconWrapper>
            {ICONS[postIconKey] || <MdArticle fontSize={16} />}
          </StyledIconWrapper>
        ),
        key: post.slug,
        path: `/${post?.organization?.domain_handle}/${post.space?.slug}/${post.slug}/`,
        isEdit: post.post_status === 'draft',
      });
    });
  }, [posts]);

  const selectedItem = useMemo(() => {
    if (postSlug) {
      return `/${orgSlug}/${spaceSlug}/${postSlug}/`;
    } else if (spaceSlug) {
      return `/${orgSlug}/${spaceSlug}/`;
    }

    return '';
  }, [orgSlug, spaceSlug, postSlug]);

  const onMenuClick = (options: { key: string }) => {
    router.push(options.key);
  };

  return (
    isAuthenticated && (
      <PageSidebar
        selectedKeys={[selectedItem]}
        defaultOpenKeys={
          currentPost?.parent_post_slug
            ? [`/${orgSlug}/${spaceSlug}/${currentPost?.parent_post_slug}/`]
            : []
        }
        items={getMenus as any}
        onMenuClick={onMenuClick}
        loading={loading}
      />
    )
  );
};

export default ThreadMenus;
