import React, { useState } from 'react';
import { Button, Form, FormItemProps, Popover, Select } from 'antd';
import { useMediaQuery } from 'react-responsive';
import { FaGlobe } from 'react-icons/fa';
import { regionOptions } from '@unpod/constants/CountryData';
import { TabWidthQuery } from '@unpod/constants';

type AppRegionFieldProps = Omit<FormItemProps, 'name'> & {
  name?: string;
  required?: boolean;};

const AppRegionField: React.FC<AppRegionFieldProps> = ({
  name = 'region',
  required = true,
  ...restProps
}) => {
  const mobileScreen = useMediaQuery(TabWidthQuery);
  const [open, setOpen] = useState(false);

  const dropdownField = (
    <Form.Item
      name={name}
      initialValue="IN"
      rules={[{ required, message: 'Region is required' }]}
      {...restProps}
    >
      <Select
        placeholder="Select region"
        options={regionOptions}
        // defaultValue={'IN'}
        style={{ minWidth: 100 }}
      />
    </Form.Item>
  );

  if (mobileScreen) {
    return (
      <Popover
        content={dropdownField}
        title="Select Region"
        trigger="click"
        open={open}
        onOpenChange={setOpen}
      >
        <Button
          icon={<FaGlobe />}
          type="default"
          style={{
            borderRadius: '50%',
            width: 36,
            height: 36,
          }}
        ></Button>
      </Popover>
    );
  }

  return dropdownField;
};

export default AppRegionField;
