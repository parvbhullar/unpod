import type { ReactNode } from 'react';
import { Fragment, useMemo, useState } from 'react';
import { MdAddCircleOutline } from 'react-icons/md';
import { useParams, useRouter } from 'next/navigation';
import { useIntl } from 'react-intl';
import AppNewSpace from '@unpod/components/modules/AppNewSpace';
import AppCustomMenus from '@unpod/components/common/AppCustomMenus';
import {
  StyledAddButton,
  StyledContent,
  StyledContentMain,
  StyledInput,
  StyledInputWrapper,
  StyledMenusContainer,
  StyledTitle,
} from './index.styled';
import { AppPopover } from '@unpod/components/antd';

type MenuItem = {
  key: string;
  label: string;
  title?: string;
  icon?: ReactNode;
  onClick?: () => void;
};

type SpaceMenuPopoverProps = {
  title: string;
  spaces: MenuItem[];
  contentType?: string;
  children?: ReactNode;
};

const SpaceMenuPopover = ({
  title,
  spaces,
  contentType,
  ...props
}: SpaceMenuPopoverProps) => {
  const router = useRouter();
  const { spaceSlug } = useParams() as { spaceSlug?: string };
  const { formatMessage } = useIntl();

  const [open, setOpen] = useState(false);
  const [addNew, setAddNew] = useState(false);
  const [search, setSearch] = useState('');

  const items = useMemo(() => {
    return search
      ? spaces.filter((space) =>
          space.label.toLowerCase().includes(search.toLowerCase()),
        )
      : spaces;
  }, [spaces, search]);

  const onSpaceCreated = (response: { data: { slug?: string } }) => {
    if (response.data.slug) {
      router.push(`/spaces/${response.data.slug}`);
    }
  };

  const onCreateClick = () => {
    setOpen(false);
    setAddNew(true);
  };

  const getContent = () => {
    return (
      <StyledMenusContainer>
        <StyledTitle>{title}</StyledTitle>
        <StyledInputWrapper>
          <StyledInput
            placeholder={formatMessage({ id: 'common.searchHere' })}
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </StyledInputWrapper>
        <StyledContent>
          {items.length === 0 ? (
            <p>{formatMessage({ id: 'space.noSpacesFound' })}</p>
          ) : (
            <StyledContentMain>
              <AppCustomMenus
                items={
                  search
                    ? spaces.filter((space) =>
                        space.label
                          .toLowerCase()
                          .includes(search.toLowerCase()),
                      )
                    : spaces
                }
                activeKeys={spaceSlug ? [spaceSlug] : []}
              />
            </StyledContentMain>
          )}
        </StyledContent>

        <StyledAddButton onClick={() => onCreateClick()}>
          <MdAddCircleOutline fontSize={16} />
          <span>{formatMessage({ id: 'space.addNew' })}</span>
        </StyledAddButton>

        {/*<StyledHubMenus
          selectedKeys={[spaceSlug]}
          mode="inline"
          items={spaces}
          onClick={onMenuClick}
        />*/}
      </StyledMenusContainer>
    );
  };

  return (
    <Fragment>
      {contentType && (
        <AppNewSpace
          content_type={contentType}
          openForm={addNew}
          setFormOpen={setAddNew}
          onSpaceCreated={onSpaceCreated}
        />
      )}
      <AppPopover
        content={getContent()}
        placement="rightTop"
        open={open}
        onOpenChange={(visible) => setOpen(visible)}
        {...props}
      />
    </Fragment>
  );
};

export default SpaceMenuPopover;
