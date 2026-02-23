'use client';

import React, {createContext, ReactNode, useContext, useEffect, useState,} from 'react';
import {useAuthContext} from '../context-provider/AuthContextProvider';

export type TourContextType = {
  showTour: boolean;
};

export type TourActionsContextType = {
  startTour: () => void;
  completeTour: () => void;
};

const TourContext = createContext<TourContextType>({showTour: false});
const TourActionsContext = createContext<TourActionsContextType | undefined>(
  undefined,
);

export const useTourContext = (): TourContextType => useContext(TourContext);
export const useTourActionsContext = (): TourActionsContextType => {
  const context = useContext(TourActionsContext);
  if (!context) {
    throw new Error(
      'useTourActionsContext must be used within TourContextProvider',
    );
  }
  return context;
};

export type TourContextProviderProps = {
  children: ReactNode;
};

export const TourContextProvider: React.FC<TourContextProviderProps> = ({
                                                                          children,
                                                                        }) => {
  const [showTour, setShowTour] = useState(false);
  const {user, isAuthenticated} = useAuthContext();

  useEffect(() => {
    // Check if user has already seen the tour
    if (isAuthenticated && user) {
      const tourCompleted = localStorage.getItem(
        `onboarding_tour_completed_${user.id}`,
      );
      if (!tourCompleted) {
        // Check if this is triggered by first agent creation
        const shouldShowTour = sessionStorage.getItem(
          `trigger_onboarding_tour_${user.id}`,
        );
        if (shouldShowTour === 'true') {
          setShowTour(true);
          sessionStorage.removeItem(`trigger_onboarding_tour_${user.id}`);
        }
      }
    }
  }, [isAuthenticated, user]);

  const startTour = (): void => {
    if (user) {
      sessionStorage.setItem(`trigger_onboarding_tour_${user.id}`, 'true');
      setShowTour(true);
    }
  };

  const completeTour = (): void => {
    if (user) {
      localStorage.setItem(`onboarding_tour_completed_${user.id}`, 'true');
      sessionStorage.removeItem(`trigger_onboarding_tour_${user.id}`);
    }
    setShowTour(false);
  };

  return (
    <TourActionsContext.Provider
      value={{
        startTour,
        completeTour,
      }}
    >
      <TourContext.Provider value={{showTour}}>
        {children}
      </TourContext.Provider>
    </TourActionsContext.Provider>
  );
};
