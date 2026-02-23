'use client';
import {useState} from 'react';

import {AppDrawer} from '@unpod/components/antd';
import {getFormattedDate} from '@unpod/helpers/DateHelper';
import {
  CallCard,
  CallCardBody,
  CallCardHeader,
  CallCardsContainer,
  CallCardsScroll,
  CallDuration,
  CallError,
  CallHeaderContent,
  CallHeaderTop,
  CallIconWrapper,
  CallPhone,
  CallStatus,
  CallTitle,
} from './index.styled';
import CardsScrollWrapper from './CardsScrollWrapper';

type CallItem = {
  id?: string | number;
  name?: string;
  status?: string;
  provider_phone?: string;
  duration_seconds?: number;
  started_at?: string;
  ended_at?: string;
  description?: string;
  error_message?: string;
};

type CallCardsData = {
  items?: CallItem[];
};

type CallCardsProps = {
  data?: CallCardsData;
};

const CallCards = ({data}: CallCardsProps) => {
  const calls = data?.items || [];
  const [selectedCall, setSelectedCall] = useState<CallItem | null>(null);

  // Helper function to format duration
  const formatDuration = (seconds?: number) => {
    if (!seconds && seconds !== 0) return '00:00';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  // Helper function to get gradient based on status
  const getStatusGradient = (status?: string) => {
    switch (status) {
      case 'active':
      case 'connected':
        return 'linear-gradient(135deg, #10B981 0%, #059669 100%)';
      case 'initiating':
        return 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)';
      case 'ringing':
        return 'linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)';
      case 'connecting':
        return 'linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%)';
      case 'ended':
        return 'linear-gradient(135deg, #10B981 0%, #059669 100%)';
      case 'failed':
        return 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)';
      default:
        return 'linear-gradient(135deg, #6B7280 0%, #4B5563 100%)';
    }
  };

  console.log('CallCards render:', data, calls);
  return (
    <CallCardsContainer>
      <CardsScrollWrapper ScrollComponent={CallCardsScroll} items={calls}>
        {calls.map((call, index) => {
          const status = call.status || 'ended';

          return (
            <CallCard
              key={call.id ?? index}
              onClick={() => setSelectedCall(call)}
            >
              <CallCardHeader $status={status}>
                <CallIconWrapper $status={status}>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path
                      d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
                  </svg>
                </CallIconWrapper>
                <CallHeaderContent>
                  <CallHeaderTop>
                    <CallTitle>{call.name}</CallTitle>
                    <CallStatus $status={status}>{status}</CallStatus>
                  </CallHeaderTop>
                  {call.provider_phone && (
                    <CallPhone>
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        width="14"
                        height="14"
                      >
                        <path
                          d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
                      </svg>
                      <a href={`tel:${call.provider_phone}`}>
                        {call.provider_phone}
                      </a>
                    </CallPhone>
                  )}
                </CallHeaderContent>
              </CallCardHeader>

              <CallCardBody>
                {/* For ended calls, show compact duration and time */}
                {status === 'ended' ? (
                  <div
                    style={{
                      display: 'flex',
                      gap: '8px',
                      alignItems: 'center',
                      flexWrap: 'wrap',
                    }}
                  >
                    {/* Started Time Chip - First (Green themed) */}
                    {call.started_at && (
                      <div
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          padding: '6px 12px',
                          background: '#F0FDF4',
                          borderRadius: '8px',
                          border: '1px solid #86EFAC',
                        }}
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="#059669"
                          strokeWidth="2"
                          width="14"
                          height="14"
                        >
                          <rect
                            x="3"
                            y="4"
                            width="18"
                            height="18"
                            rx="2"
                            ry="2"
                          ></rect>
                          <line x1="16" y1="2" x2="16" y2="6"></line>
                          <line x1="8" y1="2" x2="8" y2="6"></line>
                          <line x1="3" y1="10" x2="21" y2="10"></line>
                        </svg>
                        <span
                          style={{
                            fontSize: '13px',
                            fontWeight: 600,
                            color: '#047857',
                          }}
                        >
                          {getFormattedDate(call.started_at, 'MMM D', true)} at{' '}
                          {getFormattedDate(call.started_at, 'h:mm:ss A', true)}
                        </span>
                      </div>
                    )}

                    {/* Duration Chip - Second (Light Blue) */}
                    {call.duration_seconds !== undefined &&
                      call.duration_seconds > 0 && (
                        <div
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px',
                            padding: '6px 12px',
                            background:
                              'linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%)',
                            borderRadius: '8px',
                            border: '1px solid #93C5FD',
                          }}
                        >
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="#3B82F6"
                            strokeWidth="2"
                            width="14"
                            height="14"
                          >
                            <circle cx="12" cy="12" r="10"></circle>
                            <polyline points="12 6 12 12 16 14"></polyline>
                          </svg>
                          <span
                            style={{
                              fontSize: '13px',
                              fontWeight: 600,
                              color: '#2563EB',
                              fontFamily: 'monospace',
                            }}
                          >
                            {formatDuration(call.duration_seconds)}
                          </span>
                        </div>
                      )}
                  </div>
                ) : (
                  <>
                    {/* For active/other calls, show minimal info */}
                    {call.duration_seconds !== undefined &&
                      call.duration_seconds > 0 && (
                        <CallDuration>
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                          >
                            <circle cx="12" cy="12" r="10"></circle>
                            <polyline points="12 6 12 12 16 14"></polyline>
                          </svg>
                          Duration: {formatDuration(call.duration_seconds)}
                        </CallDuration>
                      )}

                    {call.started_at && (
                      <div
                        style={{
                          fontSize: '13px',
                          color: 'var(--text-secondary)',
                          marginTop: '8px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                        }}
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          width="14"
                          height="14"
                        >
                          <rect
                            x="3"
                            y="4"
                            width="18"
                            height="18"
                            rx="2"
                            ry="2"
                          ></rect>
                          <line x1="16" y1="2" x2="16" y2="6"></line>
                          <line x1="8" y1="2" x2="8" y2="6"></line>
                          <line x1="3" y1="10" x2="21" y2="10"></line>
                        </svg>
                        {getFormattedDate(call.started_at, 'MMM D', true)} at{' '}
                        {getFormattedDate(call.started_at, 'h:mm:ss A', true)}
                      </div>
                    )}
                  </>
                )}

                {call.error_message && (
                  <CallError>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <circle cx="12" cy="12" r="10"></circle>
                      <line x1="12" y1="8" x2="12" y2="12"></line>
                      <line x1="12" y1="16" x2="12.01" y2="16"></line>
                    </svg>
                    <span>{call.error_message}</span>
                  </CallError>
                )}
              </CallCardBody>
            </CallCard>
          );
        })}
      </CardsScrollWrapper>

      {/* Detail Drawer */}
      <AppDrawer
        open={!!selectedCall}
        onClose={() => setSelectedCall(null)}
        title="Call Details"
        closable
        placement="right"
        width={600}
      >
        {selectedCall &&
          (() => {
            const status = selectedCall.status || 'ended';

            return (
              <div>
                {/* Status Banner with gradient */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '24px',
                    background: getStatusGradient(status),
                    borderRadius: '16px',
                    marginBottom: '24px',
                    color: 'white',
                    boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1)',
                  }}
                >
                  <div>
                    <div
                      style={{
                        fontSize: '12px',
                        opacity: 0.9,
                        marginBottom: '8px',
                        textTransform: 'uppercase',
                        letterSpacing: '1px',
                        fontWeight: 600,
                      }}
                    >
                      Call Status
                    </div>
                    <div
                      style={{
                        fontSize: '24px',
                        fontWeight: 700,
                        textTransform: 'capitalize',
                      }}
                    >
                      {status}
                    </div>
                  </div>
                  <div
                    style={{
                      width: '64px',
                      height: '64px',
                      borderRadius: '50%',
                      background: 'rgba(255, 255, 255, 0.25)',
                      backdropFilter: 'blur(10px)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
                    }}
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="white"
                      strokeWidth="2.5"
                      width="36"
                      height="36"
                    >
                      <path
                        d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
                    </svg>
                  </div>
                </div>

                {/* Contact Info */}
                <div
                  style={{
                    background: '#F9FAFB',
                    borderRadius: '12px',
                    padding: '20px',
                    marginBottom: '24px',
                  }}
                >
                  <div
                    style={{
                      fontSize: '13px',
                      color: '#6B7280',
                      marginBottom: '12px',
                      fontWeight: 600,
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                    }}
                  >
                    Contact
                  </div>
                  <div
                    style={{
                      fontSize: '20px',
                      fontWeight: 700,
                      color: '#111827',
                      marginBottom: '12px',
                    }}
                  >
                    {selectedCall.name}
                  </div>
                  {selectedCall.provider_phone && (
                    <a
                      href={`tel:${selectedCall.provider_phone}`}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '10px',
                        padding: '10px 18px',
                        background: 'white',
                        border: '2px solid #4F46E5',
                        borderRadius: '10px',
                        fontSize: '16px',
                        color: '#4F46E5',
                        textDecoration: 'none',
                        fontWeight: 600,
                        transition: 'all 0.2s',
                      }}
                      onMouseOver={(e) => {
                        e.currentTarget.style.background = '#4F46E5';
                        e.currentTarget.style.color = 'white';
                      }}
                      onMouseOut={(e) => {
                        e.currentTarget.style.background = 'white';
                        e.currentTarget.style.color = '#4F46E5';
                      }}
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        width="20"
                        height="20"
                      >
                        <path
                          d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
                      </svg>
                      {selectedCall.provider_phone}
                    </a>
                  )}
                </div>

                {/* Duration Highlight */}
                {selectedCall.duration_seconds !== undefined &&
                  selectedCall.duration_seconds > 0 && (
                    <div
                      style={{
                        background:
                          'linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%)',
                        border: '2px solid #3B82F6',
                        borderRadius: '16px',
                        padding: '24px',
                        marginBottom: '24px',
                        textAlign: 'center',
                      }}
                    >
                      <div
                        style={{
                          fontSize: '13px',
                          color: '#1E40AF',
                          marginBottom: '8px',
                          fontWeight: 600,
                          textTransform: 'uppercase',
                          letterSpacing: '1px',
                        }}
                      >
                        Call Duration
                      </div>
                      <div
                        style={{
                          fontSize: '48px',
                          fontWeight: 700,
                          color: '#1E3A8A',
                          letterSpacing: '2px',
                          fontFamily: 'monospace',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '12px',
                        }}
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="#1E3A8A"
                          strokeWidth="2.5"
                          width="40"
                          height="40"
                        >
                          <circle cx="12" cy="12" r="10"></circle>
                          <polyline points="12 6 12 12 16 14"></polyline>
                        </svg>
                        {formatDuration(selectedCall.duration_seconds)}
                      </div>
                    </div>
                  )}

                {/* Call Timeline */}
                {(selectedCall.started_at || selectedCall.ended_at) && (
                  <div style={{marginBottom: '24px'}}>
                    <div
                      style={{
                        fontSize: '14px',
                        fontWeight: 700,
                        color: '#111827',
                        marginBottom: '16px',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px',
                      }}
                    >
                      Timeline
                    </div>
                    <div style={{display: 'flex', gap: '12px'}}>
                      {selectedCall.started_at && (
                        <div
                          style={{
                            flex: 1,
                            padding: '16px',
                            background: '#F0FDF4',
                            border: '2px solid #10B981',
                            borderRadius: '12px',
                          }}
                        >
                          <div
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '8px',
                              marginBottom: '8px',
                            }}
                          >
                            <svg
                              xmlns="http://www.w3.org/2000/svg"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="#059669"
                              strokeWidth="2"
                              width="20"
                              height="20"
                            >
                              <circle cx="12" cy="12" r="10"></circle>
                              <polyline points="12 6 12 12 16 14"></polyline>
                            </svg>
                            <div
                              style={{
                                fontSize: '12px',
                                color: '#065F46',
                                fontWeight: 600,
                                textTransform: 'uppercase',
                                letterSpacing: '0.5px',
                              }}
                            >
                              Started
                            </div>
                          </div>
                          <div
                            style={{
                              fontSize: '15px',
                              fontWeight: 700,
                              color: '#064E3B',
                            }}
                          >
                            {getFormattedDate(
                              selectedCall.started_at,
                              'MMM D',
                              true,
                            )}
                          </div>
                          <div
                            style={{
                              fontSize: '14px',
                              fontWeight: 600,
                              color: '#047857',
                            }}
                          >
                            {getFormattedDate(
                              selectedCall.started_at,
                              'h:mm:ss A',
                              true,
                            )}
                          </div>
                        </div>
                      )}

                      {selectedCall.ended_at && (
                        <div
                          style={{
                            flex: 1,
                            padding: '16px',
                            background: '#FEF2F2',
                            border: '2px solid #EF4444',
                            borderRadius: '12px',
                          }}
                        >
                          <div
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '8px',
                              marginBottom: '8px',
                            }}
                          >
                            <svg
                              xmlns="http://www.w3.org/2000/svg"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="#DC2626"
                              strokeWidth="2"
                              width="20"
                              height="20"
                            >
                              <circle cx="12" cy="12" r="10"></circle>
                              <line x1="15" y1="9" x2="9" y2="15"></line>
                              <line x1="9" y1="9" x2="15" y2="15"></line>
                            </svg>
                            <div
                              style={{
                                fontSize: '12px',
                                color: '#991B1B',
                                fontWeight: 600,
                                textTransform: 'uppercase',
                                letterSpacing: '0.5px',
                              }}
                            >
                              Ended
                            </div>
                          </div>
                          <div
                            style={{
                              fontSize: '15px',
                              fontWeight: 700,
                              color: '#7F1D1D',
                            }}
                          >
                            {getFormattedDate(
                              selectedCall.ended_at,
                              'MMM D',
                              true,
                            )}
                          </div>
                          <div
                            style={{
                              fontSize: '14px',
                              fontWeight: 600,
                              color: '#B91C1C',
                            }}
                          >
                            {getFormattedDate(
                              selectedCall.ended_at,
                              'h:mm:ss A',
                              true,
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Description/Notes */}
                {selectedCall.description && !selectedCall.error_message && (
                  <div
                    style={{
                      padding: '16px',
                      background: '#FFFBEB',
                      border: '1px solid #FDE68A',
                      borderRadius: '12px',
                      marginBottom: '20px',
                    }}
                  >
                    <div style={{display: 'flex', gap: '10px'}}>
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="#D97706"
                        strokeWidth="2"
                        width="20"
                        height="20"
                        style={{flexShrink: 0, marginTop: '2px'}}
                      >
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                      </svg>
                      <div style={{flex: 1}}>
                        <div
                          style={{
                            fontSize: '12px',
                            fontWeight: 600,
                            color: '#92400E',
                            marginBottom: '6px',
                            textTransform: 'uppercase',
                            letterSpacing: '0.5px',
                          }}
                        >
                          Notes
                        </div>
                        <p
                          style={{
                            fontSize: '14px',
                            lineHeight: '1.6',
                            color: '#78350F',
                            margin: 0,
                          }}
                        >
                          {selectedCall.description}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Error Message */}
                {selectedCall.error_message && (
                  <div
                    style={{
                      background:
                        'linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%)',
                      border: '2px solid #EF4444',
                      borderRadius: '12px',
                      padding: '20px',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '16px',
                      }}
                    >
                      <div
                        style={{
                          width: '48px',
                          height: '48px',
                          borderRadius: '50%',
                          background: '#EF4444',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexShrink: 0,
                        }}
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="white"
                          strokeWidth="2.5"
                          width="28"
                          height="28"
                        >
                          <circle cx="12" cy="12" r="10"></circle>
                          <line x1="12" y1="8" x2="12" y2="12"></line>
                          <line x1="12" y1="16" x2="12.01" y2="16"></line>
                        </svg>
                      </div>
                      <div style={{flex: 1}}>
                        <div
                          style={{
                            fontSize: '12px',
                            color: '#991B1B',
                            fontWeight: 600,
                            marginBottom: '4px',
                            textTransform: 'uppercase',
                            letterSpacing: '0.5px',
                          }}
                        >
                          Call Error
                        </div>
                        <div
                          style={{
                            fontSize: '14px',
                            color: '#7F1D1D',
                            lineHeight: '1.5',
                            fontWeight: 500,
                          }}
                        >
                          {selectedCall.error_message}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })()}
      </AppDrawer>
    </CallCardsContainer>
  );
};

export default CallCards;
