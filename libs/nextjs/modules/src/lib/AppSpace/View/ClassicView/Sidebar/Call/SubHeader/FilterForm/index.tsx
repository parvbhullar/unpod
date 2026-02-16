import { Button, Form } from 'antd';
import AppDateTime from '@unpod/components/antd/AppDateTime';
import Labels from './Labels';
import { CALL_FILTER_STATUS_OPTIONS, CALL_TYPE_OPTIONS } from '../data';
import { StyledActions, StyledRoot } from './index.styled';
import { useIntl } from 'react-intl';

const { Item, useForm } = Form;

type FilterFormProps = {
  filters: Record<string, unknown>;
  onApplyFilters: (filters: Record<string, unknown> | null) => void;
  clearFilter: () => void;
};

const FilterForm = ({
  filters,
  onApplyFilters,
  clearFilter,
}: FilterFormProps) => {
  const [form] = useForm();
  const { formatMessage } = useIntl();

  const onFinish = (values: Record<string, unknown>) => {
    onApplyFilters(values);
  };

  const onClear = () => {
    form.resetFields();
    onApplyFilters(null);
    clearFilter();
  };

  return (
    <StyledRoot>
      <Form
        form={form}
        onFinish={onFinish}
        initialValues={filters}
        layout="vertical"
      >
        <Item
          name="call_type"
          label={formatMessage({ id: 'callLogs.callType' })}
        >
          <Labels data={CALL_TYPE_OPTIONS} />
        </Item>

        <Item name="status" label={formatMessage({ id: 'callLogs.status' })}>
          <Labels data={CALL_FILTER_STATUS_OPTIONS} multiSelect />
        </Item>

        <Item
          name="from_ts"
          label={formatMessage({ id: 'filterForm.callScheduleTime' })}
        >
          <AppDateTime
            placeholder={formatMessage({ id: 'downloadLogs.from' })}
            showTime={{ format: 'HH:mm:ss' }}
            format="DD-MM-YYYY HH:mm:ss"
          />
        </Item>

        <Item name="to_ts">
          <AppDateTime
            placeholder={formatMessage({ id: 'downloadLogs.to' })}
            showTime={{ format: 'HH:mm:ss' }}
            format="DD-MM-YYYY HH:mm:ss"
          />
        </Item>

        <StyledActions>
          <Button type="default" htmlType="button" onClick={onClear}>
            {formatMessage({ id: 'common.clear' })}
          </Button>

          <Button type="primary" htmlType="submit">
            {formatMessage({ id: 'common.apply' })}
          </Button>
        </StyledActions>
      </Form>
    </StyledRoot>
  );
};

export default FilterForm;
