'use client';
import React, {useEffect, useRef} from 'react';
import {driver, Driver, DriveStep} from 'driver.js';
import 'driver.js/dist/driver.css';
import './tour.css';
import {useAuthContext} from '@unpod/providers';
import {useRouter} from 'next/navigation';

type OnboardingTourProps = {
  isOpen: boolean;
  onComplete?: () => void;
};

const OnboardingTour: React.FC<OnboardingTourProps> = ({
                                                         isOpen,
                                                         onComplete,
                                                       }) => {
  const driverRef = useRef<Driver | null>(null);
  const {user} = useAuthContext();
  const spaceSlug = user?.active_space?.slug;
  const router = useRouter();

  useEffect(() => {
    if (!isOpen || !spaceSlug) return;

    // Check if we have a saved tour state
    const savedStep = sessionStorage.getItem('onboarding-tour-step');
    const startStep = savedStep ? parseInt(savedStep, 10) : 0;

    // All tour steps - studio steps are always included
    const allSteps: DriveStep[] = [
      {
        popover: {
          title: 'Welcome to Your AI Workspace!',
          description:
            "Congratulations on creating your first AI agent! Let's take a quick tour of the main navigation menu to help you get started.",
          side: 'right' as const,
          align: 'start' as const,
        },
      },
      {
        element: '.org-avatar',
        popover: {
          title: 'Organization Hub',
          description:
            'This is your organization hub. Click here to switch between different organizations or workspaces you have access to.',
          side: 'right' as const,
          align: 'start' as const,
        },
      },
      {
        element: '[data-tour="calls"]',
        popover: {
          title: 'Calls',
          description:
            'Access call history and manage voice/video calls with your AI agents. Review past calls, join active sessions, and track call analytics.',
          side: 'right' as const,
          align: 'start' as const,
        },
      },
      {
        element: `a[href="/spaces/${spaceSlug}/doc/"]`,
        popover: {
          title: 'People',
          description:
            'Manage your contacts, people, and their related information. Store profiles, communication history, and all relevant data about the people you interact with.',
          side: 'right' as const,
          align: 'start' as const,
        },
      },
      {
        element: `a[href="/spaces/${spaceSlug}/analytics/"]`,
        popover: {
          title: 'Analytics',
          description:
            'Monitor performance metrics and gain insights about your AI agents and workspace activities. Track usage patterns and measure success.',
          side: 'right' as const,
          align: 'start' as const,
        },
      },
      {
        element: '[data-tour="studio-view"]',
        popover: {
          title: 'Toggle View',
          description: `Toggle between Space View and Studio View. Studio View gives you an enhanced agent management experience with advanced tools and organization settings. <br/><br/><button class="driver-popover-next-btn" id="switch-to-studio-btn" style=" cursor: pointer"  >Switch to Studio View</button>`,
          side: 'right' as const,
          align: 'start' as const,
        },
      },
      // Studio view menu items
      {
        element: '[data-tour="admin-dashboard"]',
        popover: {
          title: 'Dashboard',
          description:
            'Your organization dashboard. View key metrics, recent activity, and manage your workspace from this central hub.',
          side: 'right' as const,
          align: 'start' as const,
        },
      },
      {
        element: '[data-tour="admin-ai-studio"]',
        popover: {
          title: 'AI Studio',
          description:
            'Create and manage your AI agents. Configure their behavior, knowledge bases, and integrations to build powerful AI assistants.',
          side: 'right' as const,
          align: 'start' as const,
        },
      },
      {
        element: '[data-tour="admin-knowledge-bases"]',
        popover: {
          title: 'Knowledge Base',
          description:
            'Upload and manage documents, files, and knowledge sources for your AI agents. Build a comprehensive knowledge base to enhance agent capabilities.',
          side: 'right' as const,
          align: 'start' as const,
        },
      },
      {
        element: '[data-tour="admin-call-logs"]',
        popover: {
          title: 'Call Logs',
          description:
            'Review detailed call history, recordings, and transcripts. Track all voice and video interactions with your AI agents.',
          side: 'right' as const,
          align: 'start' as const,
        },
      },
      {
        element: '[data-tour="admin-api-keys"]',
        popover: {
          title: 'API Keys',
          description:
            'Generate and manage API keys for integrating your AI agents with external applications and services.',
          side: 'right' as const,
          align: 'start' as const,
        },
      },
      // Common ending steps
      {
        element: '[data-tour="notifications"]',
        popover: {
          title: 'Notifications',
          description:
            'Stay updated with important alerts and notifications. Get notified about agent activities, system updates, and workspace events in real-time.',
          side: 'right' as const,
          align: 'start' as const,
        },
      },
      {
        element: '[data-tour="profile"]',
        popover: {
          title: 'Profile & Settings',
          description:
            'Access your profile, account settings, billing, and wallet. You can also sign out from here.',
          side: 'right' as const,
          align: 'start' as const,
        },
      },
      {
        popover: {
          title: "You're All Set!",
          description:
            'You now know the basics of navigating your AI workspace. Feel free to explore and make the most of your AI agents. You can always access help from the user menu at the bottom of the sidebar.',
          side: 'right' as const,
          align: 'start' as const,
        },
      },
    ];

    // Initialize driver.js
    const driverObj = driver({
      showProgress: true,
      showButtons: ['next', 'previous', 'close'],
      onHighlightStarted: (element, step, options) => {
        // Save current step to session storage
        const stepIndex = options.state.activeIndex;
        if (stepIndex !== undefined) {
          sessionStorage.setItem('onboarding-tour-step', stepIndex.toString());
        }
      },
      onNextClick: (element, step, options) => {
        const stepIndex = options.state.activeIndex;

        // If on Toggle View step (index 5) and user clicks Next without switching
        if (stepIndex === 5) {
          // Check if we're still in space view (not studio view)
          const isStudioView =
            window.location.pathname.startsWith('/org') ||
            window.location.pathname.startsWith('/ai-studio') ||
            window.location.pathname.startsWith('/knowledge-bases') ||
            window.location.pathname.startsWith('/call-logs') ||
            window.location.pathname.startsWith('/api-keys');

          if (!isStudioView) {
            // Skip studio view steps (6-10) and go to Notifications (index 11)
            driverObj.drive(11);
            return;
          }
        }

        // Default behavior: move to next step
        driverObj.moveNext();
      },
      nextBtnText: `
        <span class="tour-btn-content">
          <span class="tour-btn-text">Next</span>
          <svg class="tour-btn-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="9 18 15 12 9 6"></polyline>
          </svg>
        </span>
      `,
      prevBtnText: `
        <span class="tour-btn-content">
          <svg class="tour-btn-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="15 18 9 12 15 6"></polyline>
          </svg>
          <span class="tour-btn-text">Previous</span>
        </span>
      `,
      doneBtnText: `
        <span class="tour-btn-content">
          <span class="tour-btn-text">Get Started</span>
          <svg class="tour-btn-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        </span>
      `,
      steps: allSteps,
      onDestroyStarted: () => {
        // Clear saved tour state when tour is completed or closed
        sessionStorage.removeItem('onboarding-tour-step');
        if (driverObj) {
          driverObj.destroy();
        }
        if (onComplete) {
          onComplete();
        }
      },
      popoverClass: 'driverjs-theme',
      stagePadding: 8,
      stageRadius: 12,
      onPopoverRender: (popover, {config, state}) => {
        // Add custom close button with icon
        const closeBtn = popover.wrapper.querySelector(
          '.driver-popover-close-btn',
        );
        if (closeBtn) {
          closeBtn.innerHTML = `
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          `;
        }

        // Handle studio view switch button
        const switchBtn = popover.wrapper.querySelector(
          '#switch-to-studio-btn',
        ) as HTMLElement | null;
        if (switchBtn) {
          switchBtn.onclick = () => {
            // Save the next step (Dashboard - index 6) before navigation
            sessionStorage.setItem('onboarding-tour-step', '6');
            // Navigate to studio view
            router.push('/org/');
          };
        }
      },
    });

    driverRef.current = driverObj;

    // Small delay to ensure DOM is ready
    const timer = setTimeout(() => {
      if (startStep > 0) {
        // Resume from saved step
        driverObj.drive(startStep);
      } else {
        // Start from beginning
        driverObj.drive();
      }
    }, 500);

    return () => {
      clearTimeout(timer);
      if (driverRef.current) {
        driverRef.current.destroy();
      }
    };
  }, [isOpen, spaceSlug, onComplete]);

  return null;
};

export default OnboardingTour;
