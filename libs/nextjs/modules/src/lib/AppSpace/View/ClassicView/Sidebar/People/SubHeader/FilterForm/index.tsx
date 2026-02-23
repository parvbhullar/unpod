import type {ReactNode} from 'react';
import {Button, Form} from 'antd';
import AppDateTime from '@unpod/components/antd/AppDateTime';
import Labels from './Labels';
import {StyledActions, StyledRoot} from './index.styled';
import {useIntl} from 'react-intl';

const {Item, useForm} = Form;

type FilterFormProps = {
  tags: Array<{ slug?: string; name?: string; icon?: ReactNode }>;
  filters?: Record<string, any>;
  onApplyFilters: (values: Record<string, any> | null) => void;
  clearFilter: () => void;
};

const FilterForm = ({
                      tags,
                      filters,
                      onApplyFilters,
                      clearFilter,
                    }: FilterFormProps) => {
  const [form] = useForm();
  const {formatMessage} = useIntl();

  const onFinish = (values: Record<string, any>) => {
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
        <Item name="tag" label={formatMessage({id: 'space.labels'})}>
          <Labels data={tags} onChange={() => null}/>
        </Item>

        {/*<Item name="status" label="Status">
          <Labels data={STATUS_OPTIONS} />
        </Item>*/}

        <Item
          name="from_ts"
          label={formatMessage({id: 'common.createdTime'})}
        >
          <AppDateTime
            placeholder={formatMessage({id: 'downloadLogs.from'})}
            showTime={{format: 'HH:mm:ss'}}
            format="DD-MM-YYYY HH:mm:ss"
          />
        </Item>

        <Item name="to_ts">
          <AppDateTime
            placeholder={formatMessage({id: 'downloadLogs.to'})}
            showTime={{format: 'HH:mm:ss'}}
            format="DD-MM-YYYY HH:mm:ss"
          />
        </Item>

        <StyledActions>
          <Button type="default" htmlType="button" onClick={onClear}>
            {formatMessage({id: 'common.clear'})}
          </Button>

          <Button type="primary" htmlType="submit">
            {formatMessage({id: 'common.apply'})}
          </Button>
        </StyledActions>
      </Form>
    </StyledRoot>
  );
};

export default FilterForm;
