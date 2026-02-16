import styled from 'styled-components';
import { Card, Form, Input, Row, Typography } from 'antd';

// Title of the form section
export const FormTitle = styled(Typography.Title)`
  margin-bottom: 10px;
  font-size: 14px;
`;

// Subtext under the title
export const SubText = styled.p`
  color: #6b7280;
  margin-bottom: 24px;
  font-size: 18px;

  @media (max-width: 768px) {
    font-size: 16px;
  }
`;

// Grid of provider cards
export const ProviderGrid = styled(Row)`
  margin-bottom: 32px;

  @media (max-width: 768px) {
    gap: 16px 0;
  }
`;

// Single provider card
export const ProviderCard = styled(Card)<{ isSelected?: boolean }>`
  text-align: center;
  border: 2px solid ${({ isSelected }) => (isSelected ? '#4f46e5' : '#f0f0f0')};
  background-color: ${({ isSelected }) => (isSelected ? '#f5f8ff' : '#fff')};
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: #4f46e5;
  }
`;

// Icon container
export const ProviderIconWrapper = styled.div`
  text-align: center;
  margin-bottom: 8px;
`;

// Title inside card
export const ProviderTitle = styled.p`
  font-weight: 500;
  font-size: 20px;
  margin-bottom: 6px;

  @media (max-width: 768px) {
    font-size: 18px;
  }
`;

// Description inside card
export const ProviderDesc = styled.p`
  font-size: 15px;
  color: #7c7c7c;

  @media (max-width: 768px) {
    font-size: 14px;
  }
`;

// Section containing the form
export const FormSection = styled.div`
  background: #fafafa;
  padding: 24px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;

  @media (max-width: 768px) {
    padding: 16px;
  }
`;

// Input field
export const StyledInput = styled(Input)`
  margin-bottom: 16px;
  height: 44px;

  @media (max-width: 480px) {
    height: 40px;
  }
`;

// Submit button
export const StyledButton = styled.button`
  margin-top: 8px;
  background-color: #22c55e;
  border: none;
  color: white;
  font-weight: 500;
  padding: 8px 16px;
  height: 40px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    background-color: #16a34a !important;
  }

  @media (max-width: 480px) {
    width: 100%;
  }
`;

// Tab wrapper
export const TabContainer = styled.div`
  display: flex;
  gap: 40px;
  margin-bottom: 32px;
  flex-wrap: wrap;

  @media (max-width: 480px) {
    gap: 16px;
  }
`;

// Inactive tab
export const Tab = styled.div`
  color: #6b7280;
  font-weight: 500;
  cursor: pointer;
  padding-bottom: 8px;
  border-bottom: 2px solid transparent;

  &:hover {
    color: #000;
  }
`;

// Active tab
export const ActiveTab = styled(Tab)`
  color: #000;
  border-color: #4f46e5;
`;

// Custom form layout
export const StyledForm = styled(Form)`
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;

  .ant-form-item {
    width: 49%;

    &:last-of-type {
      width: 100%;
    }

    @media (max-width: 768px) {
      width: 100%;
    }
  }
`;
