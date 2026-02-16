import { MdLockOutline, MdPublic } from 'react-icons/md';
import { RiUserSharedLine } from 'react-icons/ri';

export const SHARED_OPTIONS = [
  {
    key: 'private',
    label: 'permissionPopover.private',
    description: 'permissionPopover.privateDescription',
    image: (
      <span>
        <MdLockOutline fontSize={32} />
      </span>
    ),
    /* icon: (
      <span
        className="anticon"

      >
        <MdLockOutline fontSize={21} />
      </span>
    ),*/
  },
  {
    key: 'shared',
    label: 'permissionPopover.shared',
    description: 'permissionPopover.sharedDescription',
    image: (
      <span>
        <RiUserSharedLine fontSize={32} />
      </span>
    ),
    /* icon: (
      <span
        className="anticon"

      >
        <RiUserSharedLine fontSize={21} />
      </span>
    ),*/
  },
];

export const LINK_OPTIONS = {
  key: 'link',
  label: 'permissionPopover.link',
  description: 'permissionPopover.linkDescription',
  image: (
    <span>
      <MdPublic fontSize={32} />
    </span>
  ),
  /* icon: (
    <span
      className="anticon"
      css={`
        vertical-align: middle;
      `}
    >
      <MdPublic fontSize={21} />
    </span>
  ),*/
};

export const PUBLIC_OPTIONS = {
  key: 'public',
  label: 'permissionPopover.public',
  description: 'permissionPopover.publicDescription',
  image: (
    <span>
      <MdPublic fontSize={32} />
    </span>
  ),
  /* icon: (
    <span
      className="anticon"
      css={`
        vertical-align: middle;
      `}
    >
      <MdPublic fontSize={21} />
    </span>
  ),*/
};

export const getSharedOptions = (type: string) => {
  switch (type) {
    case 'chat':
    case 'note':
    case 'doc':
      return [...SHARED_OPTIONS, LINK_OPTIONS, PUBLIC_OPTIONS];
    case 'space':
      return [...SHARED_OPTIONS, PUBLIC_OPTIONS];
    case 'org':
      return [
        PUBLIC_OPTIONS,
        ...SHARED_OPTIONS.filter((item) => item.key !== 'private'),
      ];
    default:
      return [];
  }
};
// @ts-nocheck
