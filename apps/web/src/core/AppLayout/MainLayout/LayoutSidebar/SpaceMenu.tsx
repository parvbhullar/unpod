import type { Dispatch, SetStateAction } from 'react';
import { useMemo } from 'react';
import clsx from 'clsx';
import { MdOutlineWorkspaces } from 'react-icons/md';
import SpaceMenuPopover from './SpaceMenuPopover';
import { StyledMiniAvatar } from './index.styled';
import { getPostIcon } from '@unpod/helpers/PermissionHelper';
import type { Spaces } from '@unpod/constants/types';

type SpaceCollectionKey = 'documents' | 'emails' | 'contacts';

type SpaceMenuItem = {
  title: string;
  contentType: string;
  collection: SpaceCollectionKey;
  icon: JSX.Element;
  className: string;
};

export const spaceMenuItems: SpaceMenuItem[] = [
  /*  {
    title: 'Documents',
    contentType: 'general',
    collection: 'documents',
    icon: <IoDocumentsOutline fontSize={24} />,
    className: 'space-docs',
  },
  {
    title: 'Emails',
    contentType: 'email',
    collection: 'emails',
    icon: <MdOutlineEmail fontSize={21} />,
    className: 'space-emails',
  },*/
  {
    title: 'Spaces',
    contentType: 'contact',
    collection: 'contacts',
    icon: <MdOutlineWorkspaces fontSize={22} />,
    className: 'space-contacts',
  },
];

type SpaceMenuProps = {
  activeSpace: string | null;
  spaces: Spaces[];
  onSpaceClick: (space: Spaces) => void;
  spaceSlug?: string;
  setActiveSpace: Dispatch<SetStateAction<string | null>>;
};

export const SpaceMenu = ({
  activeSpace,
  spaces,
  onSpaceClick,
  spaceSlug,
  setActiveSpace,
}: SpaceMenuProps) => {
  type MenuItem = {
    key: string;
    label: string;
    title: string;
    icon: JSX.Element;
    onClick: () => void;
  };

  const spaceData = useMemo<Record<SpaceCollectionKey, MenuItem[]>>(() => {
    const getItem = (space: Spaces) => {
      if (spaceSlug && spaceSlug === space.slug) {
        setActiveSpace(space.content_type ?? null);
      }

      return {
        key: space.slug || '',
        label: space.name || '',
        title: space.name || '',
        icon: (
          <span className="ant-icon edit-icon">
            {getPostIcon(space.privacy_type ?? 'public')}
          </span>
        ),
        onClick: () => onSpaceClick(space),
      };
    };

    return spaces.reduce<Record<SpaceCollectionKey, MenuItem[]>>(
      (acc, space) => {
        if (space.content_type === 'general') {
          acc.documents.push(getItem(space));
        } else if (space.content_type === 'email') {
          acc.emails.push(getItem(space));
        } else if (space.content_type === 'contact') {
          acc.contacts.push(getItem(space));
        }
        return acc;
      },
      { documents: [], emails: [], contacts: [] },
    );
  }, [spaces, spaceSlug]);

  return (
    <>
      {spaceMenuItems.map((item) => {
        const spaces = spaceData?.[item.collection] || [];
        return (
          <SpaceMenuPopover
            title={item.title}
            spaces={spaces}
            contentType={item.contentType}
            key={item.contentType}
          >
            <StyledMiniAvatar
              icon={item.icon}
              className={clsx(item.className, {
                active: activeSpace === item.contentType,
              })}
            />
          </SpaceMenuPopover>
        );
      })}
    </>
  );
};
