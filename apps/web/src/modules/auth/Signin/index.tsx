'use client';
import React, { useState } from 'react';
import OTPVerification from '../OTPVerification';
import SignInForm from './SignInForm';
import { FlipCard, FlipContainer } from '../auth.styled';

const SignIn = () => {
  const [verifyEmail, setVerifyEmail] = useState(false);
  const [email, setEmail] = useState('');

  return (
    <FlipContainer>
      {verifyEmail ? (
        <FlipCard $flipType="in">
          <OTPVerification email={email} setEmail={setEmail} />
        </FlipCard>
      ) : (
        <SignInForm
          setEmail={setEmail}
          setVerifyEmail={setVerifyEmail}
          email={email}
        />
      )}
    </FlipContainer>
  );
};

export default SignIn;
