import '@testing-library/jest-dom';
import {screen} from '@testing-library/react';
import {renderWithWrapper} from '@mi/core';
import AppInputNumber from './index';

describe('AppInputNumber', () => {
  test('should render successfully', () => {
    const {baseElement} = renderWithWrapper(
      <AppInputNumber
        placeholder="Enter Title"
        className="my-custom-input"
        defaultValue={25}
      />
    );
    const inputContainer = baseElement.querySelector('.my-custom-input');
    expect(inputContainer.classList.contains('app-input-number')).toBe(true);

    const floatContainer = screen.getByRole('float-container', {});
    expect(floatContainer).toBeInTheDocument();

    expect(floatContainer).toEqual(inputContainer);

    const inputBox = screen.getByRole('spinbutton', {});
    expect(inputBox).toBeInTheDocument();
    expect(inputBox).toBeEnabled();

    const increaseButton = screen.getByRole('button', {
      name: /increase/i,
      exact: false,
    });
    expect(increaseButton).toBeInTheDocument();

    const decreaseButton = screen.getByRole('button', {
      name: /decrease/i,
      exact: false,
    });
    expect(decreaseButton).toBeInTheDocument();

    const upIcon = screen.getByRole('img', {name: 'up'});
    const downIcon = screen.getByRole('img', {name: 'down'});

    expect(upIcon).toBeInTheDocument();
    expect(downIcon).toBeInTheDocument();
  });

  test('Should render disabled text input successfully', () => {
    renderWithWrapper(<AppInputNumber placeholder="Enter Title" disabled/>);

    const dateInput = screen.getByRole('spinbutton', {});
    expect(dateInput).toBeInTheDocument();
    expect(dateInput).toBeDisabled();
  });

  test('Should render asterisk text input successfully', () => {
    renderWithWrapper(<AppInputNumber placeholder="Enter Title" asterisk/>);

    const dateInput = screen.getByRole('asterisk', {name: 'asterisk'});
    expect(dateInput).toBeInTheDocument();
  });

  test('Placeholder should be present', () => {
    renderWithWrapper(<AppInputNumber placeholder="Enter Title" asterisk/>);

    const placeholder = screen.getByRole('label-placeholder', {});
    expect(placeholder).toBeInTheDocument();
    expect(placeholder.textContent.includes('Enter Title')).toBe(true);
  });
});
