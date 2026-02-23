import {Typography} from 'antd';
import {MdOutlineZoomIn} from 'react-icons/md';
import {truncateString} from '@unpod/helpers/StringHelper';
import {StyledCellContent, StyledZoomContainer} from './index.styled';

const {Paragraph} = Typography;

type AppColumnZoomCellProps = {
  title?: string;
  value?: unknown;
  setSelectedCol?: (data: { title?: string; content: string }) => void;
};

const AppColumnZoomCell: React.FC<AppColumnZoomCellProps> = ({
                                                               title,
                                                               value,
                                                               setSelectedCol,
                                                             }) => {
  const displayValue =
    typeof value === 'string'
      ? truncateString(value, 50)
      : typeof value === 'object'
        ? JSON.stringify(value)
        : value != null
          ? String(value)
          : '';

  return (
    <StyledCellContent>
      <Paragraph
        className="mb-0"
        style={{margin: 0, maxWidth: 300}}
        ellipsis={{
          rows: 1,
        }}
      >
        {displayValue}
      </Paragraph>

      {value != null && setSelectedCol ? (
        <StyledZoomContainer
          onClick={() =>
            setSelectedCol?.({
              title,
              content:
                typeof value === 'object'
                  ? JSON.stringify(value)
                  : String(value),
            })
          }
        >
          <MdOutlineZoomIn fontSize={20}/>
        </StyledZoomContainer>
      ) : null}
    </StyledCellContent>
  );
};

export default AppColumnZoomCell;
