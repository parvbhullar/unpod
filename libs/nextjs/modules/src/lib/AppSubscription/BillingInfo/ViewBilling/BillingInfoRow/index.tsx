import { StyledFlexContainer, StyledLabel, StyledValue } from './index.styled';

const BillingInfoRow = ({
  label,
  value = '-',
}: {
  label: string;
  value?: any;
}) => {
  const isHtml = /<\/?[a-z][\s\S]*>/i.test(value);
  return (
    <StyledFlexContainer>
      <StyledLabel type="secondary">{label}:-</StyledLabel>
      {isHtml ? (
        <StyledValue
          as="div"
          style={{
            whiteSpace: 'normal',
            overflowWrap: 'anywhere',
            wordBreak: 'break-word',
          }}
          dangerouslySetInnerHTML={{ __html: value }}
        />
      ) : (
        <StyledValue
          ellipsis={{
            rows: 2,
            tooltip: true,
          }}
        >
          {value}
        </StyledValue>
      )}
    </StyledFlexContainer>
  );
};

export default BillingInfoRow;
