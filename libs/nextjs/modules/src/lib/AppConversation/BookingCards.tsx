'use client';
import {useState} from 'react';
import {AppDrawer} from '@unpod/components/antd';
import {
  BookingCard,
  BookingCardBody,
  BookingCardHeader,
  BookingCardsContainer,
  BookingCardsScroll,
  BookingConfirmationCode,
  BookingHeaderTop,
  BookingInfoRow,
  BookingInfoValue,
  BookingStatus,
  BookingTitle,
} from './index.styled';
import CardsScrollWrapper from './CardsScrollWrapper';

type BookingRequest = {
  provider_name?: string;
  requested_time?: string;
  requested_time_str?: string;
  service_type?: string;
  provider_phone?: string;
  user_name?: string;
  user_contact?: string;
  notes?: string;
};

type BookingItem = {
  id?: string | number;
  name?: string;
  status?: string;
  confirmation_code?: string;
  description?: string;
  error_message?: string;
  created_at?: string;
  confirmed_time?: string;
  request?: BookingRequest;
};

type BookingCardsData = {
  items?: BookingItem[];
};

type BookingCardsProps = {
  data?: BookingCardsData;
};

const BookingCards = ({data}: BookingCardsProps) => {
  const bookings = data?.items || [];
  const [selectedBooking, setSelectedBooking] = useState<BookingItem | null>(
    null,
  );

  return (
    <BookingCardsContainer>
      <CardsScrollWrapper ScrollComponent={BookingCardsScroll} items={bookings}>
        {bookings.map((booking, index) => {
          const request = booking.request || {};
          const status = booking.status || 'pending';

          return (
            <BookingCard
              key={booking.id || index}
              onClick={() => setSelectedBooking(booking)}
            >
              <BookingCardHeader $status={status}>
                <BookingHeaderTop>
                  <BookingTitle>
                    {request.provider_name || booking.name}
                  </BookingTitle>
                  <BookingStatus $status={status}>{status}</BookingStatus>
                </BookingHeaderTop>
              </BookingCardHeader>

              <BookingCardBody>
                {/* Only show essential info in card */}
                {request.requested_time && (
                  <BookingInfoRow>
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
                    <BookingInfoValue>
                      {new Date(request.requested_time).toLocaleDateString(
                        'en-US',
                        {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                        },
                      )}{' '}
                      at{' '}
                      {new Date(request.requested_time).toLocaleTimeString(
                        'en-US',
                        {
                          hour: 'numeric',
                          minute: '2-digit',
                        },
                      )}
                    </BookingInfoValue>
                  </BookingInfoRow>
                )}

                {request.service_type && (
                  <BookingInfoRow>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                      <polyline points="14 2 14 8 20 8"></polyline>
                      <line x1="16" y1="13" x2="8" y2="13"></line>
                      <line x1="16" y1="17" x2="8" y2="17"></line>
                    </svg>
                    <BookingInfoValue>{request.service_type}</BookingInfoValue>
                  </BookingInfoRow>
                )}

                {booking.confirmation_code && status === 'confirmed' && (
                  <BookingConfirmationCode>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      width="16"
                      height="16"
                    >
                      <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    {booking.confirmation_code}
                  </BookingConfirmationCode>
                )}
              </BookingCardBody>
            </BookingCard>
          );
        })}
      </CardsScrollWrapper>

      {/* Detail Drawer */}
      <AppDrawer
        open={!!selectedBooking}
        onClose={() => setSelectedBooking(null)}
        title="Booking Details"
        closable
        placement="right"
        width={600}
      >
        {selectedBooking &&
          (() => {
            const request = selectedBooking.request || {};
            const status = selectedBooking.status || 'pending';

            return (
              <div>
                {/* Status Banner */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '20px',
                    background:
                      status === 'confirmed'
                        ? 'linear-gradient(135deg, #10B981 0%, #059669 100%)'
                        : status === 'pending'
                          ? 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)'
                          : 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)',
                    borderRadius: '12px',
                    marginBottom: '24px',
                    color: 'white',
                  }}
                >
                  <div>
                    <div
                      style={{
                        fontSize: '12px',
                        opacity: 0.9,
                        marginBottom: '4px',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px',
                      }}
                    >
                      Status
                    </div>
                    <div
                      style={{
                        fontSize: '20px',
                        fontWeight: 700,
                        textTransform: 'capitalize',
                      }}
                    >
                      {status}
                    </div>
                  </div>
                  <div
                    style={{
                      width: '50px',
                      height: '50px',
                      borderRadius: '50%',
                      background: 'rgba(255, 255, 255, 0.2)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="white"
                      strokeWidth="2"
                      width="28"
                      height="28"
                    >
                      {status === 'confirmed' ? (
                        <polyline points="20 6 9 17 4 12"></polyline>
                      ) : status === 'pending' ? (
                        <>
                          <circle cx="12" cy="12" r="10"></circle>
                          <polyline points="12 6 12 12 16 14"></polyline>
                        </>
                      ) : (
                        <>
                          <circle cx="12" cy="12" r="10"></circle>
                          <line x1="15" y1="9" x2="9" y2="15"></line>
                          <line x1="9" y1="9" x2="15" y2="15"></line>
                        </>
                      )}
                    </svg>
                  </div>
                </div>

                {/* Provider & Service */}
                <div
                  style={{
                    background: '#F9FAFB',
                    borderRadius: '12px',
                    padding: '20px',
                    marginBottom: '20px',
                  }}
                >
                  <div
                    style={{
                      fontSize: '13px',
                      color: '#6B7280',
                      marginBottom: '8px',
                      fontWeight: 600,
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                    }}
                  >
                    Provider
                  </div>
                  <div
                    style={{
                      fontSize: '20px',
                      fontWeight: 700,
                      color: '#111827',
                      marginBottom: '12px',
                    }}
                  >
                    {request.provider_name || selectedBooking.name}
                  </div>
                  {request.service_type && (
                    <div
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '8px 16px',
                        background: 'white',
                        borderRadius: '8px',
                        fontSize: '14px',
                        fontWeight: 600,
                        color: '#4F46E5',
                        border: '1px solid #E5E7EB',
                      }}
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        width="16"
                        height="16"
                      >
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                        <line x1="16" y1="13" x2="8" y2="13"></line>
                        <line x1="16" y1="17" x2="8" y2="17"></line>
                      </svg>
                      {request.service_type}
                    </div>
                  )}
                </div>

                {/* Appointment Time */}
                {request.requested_time && (
                  <div
                    style={{
                      background:
                        'linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%)',
                      borderRadius: '12px',
                      padding: '20px',
                      marginBottom: '20px',
                      border: '1px solid #C7D2FE',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        marginBottom: '8px',
                      }}
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="#4F46E5"
                        strokeWidth="2"
                        width="24"
                        height="24"
                      >
                        <circle cx="12" cy="12" r="10"></circle>
                        <polyline points="12 6 12 12 16 14"></polyline>
                      </svg>
                      <div
                        style={{
                          fontSize: '13px',
                          color: '#4F46E5',
                          fontWeight: 600,
                          textTransform: 'uppercase',
                          letterSpacing: '0.5px',
                        }}
                      >
                        Appointment Time
                      </div>
                    </div>
                    <div
                      style={{
                        fontSize: '18px',
                        fontWeight: 700,
                        color: '#1E1B4B',
                        marginLeft: '36px',
                      }}
                    >
                      {new Date(request.requested_time).toLocaleDateString(
                        'en-US',
                        {
                          weekday: 'long',
                          month: 'long',
                          day: 'numeric',
                          year: 'numeric',
                        },
                      )}
                    </div>
                    <div
                      style={{
                        fontSize: '16px',
                        fontWeight: 600,
                        color: '#4338CA',
                        marginLeft: '36px',
                        marginTop: '4px',
                      }}
                    >
                      {new Date(request.requested_time).toLocaleTimeString(
                        'en-US',
                        {
                          hour: 'numeric',
                          minute: '2-digit',
                        },
                      )}
                      {request.requested_time_str && (
                        <span
                          style={{
                            fontSize: '14px',
                            fontWeight: 500,
                            color: '#6366F1',
                            marginLeft: '8px',
                          }}
                        >
                          ({request.requested_time_str})
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* Contact Information */}
                {(request.provider_phone ||
                  request.user_name ||
                  request.user_contact) && (
                  <div style={{marginBottom: '20px'}}>
                    <div
                      style={{
                        fontSize: '14px',
                        fontWeight: 700,
                        color: '#111827',
                        marginBottom: '12px',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px',
                      }}
                    >
                      Contact Information
                    </div>
                    <div
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '10px',
                      }}
                    >
                      {request.provider_phone && (
                        <div
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '12px',
                            padding: '12px 16px',
                            background: '#F9FAFB',
                            borderRadius: '8px',
                          }}
                        >
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="#4F46E5"
                            strokeWidth="2"
                            width="20"
                            height="20"
                          >
                            <path
                              d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
                          </svg>
                          <div style={{flex: 1}}>
                            <div
                              style={{
                                fontSize: '12px',
                                color: '#6B7280',
                                marginBottom: '2px',
                              }}
                            >
                              Provider Phone
                            </div>
                            <a
                              href={`tel:${request.provider_phone}`}
                              style={{
                                fontSize: '15px',
                                color: '#4F46E5',
                                textDecoration: 'none',
                                fontWeight: 600,
                              }}
                            >
                              {request.provider_phone}
                            </a>
                          </div>
                        </div>
                      )}

                      {request.user_name && (
                        <div
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '12px',
                            padding: '12px 16px',
                            background: '#F9FAFB',
                            borderRadius: '8px',
                          }}
                        >
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="#6B7280"
                            strokeWidth="2"
                            width="20"
                            height="20"
                          >
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                            <circle cx="12" cy="7" r="4"></circle>
                          </svg>
                          <div style={{flex: 1}}>
                            <div
                              style={{
                                fontSize: '12px',
                                color: '#6B7280',
                                marginBottom: '2px',
                              }}
                            >
                              Your Name
                            </div>
                            <div
                              style={{
                                fontSize: '15px',
                                color: '#111827',
                                fontWeight: 600,
                              }}
                            >
                              {request.user_name}
                            </div>
                          </div>
                        </div>
                      )}

                      {request.user_contact && (
                        <div
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '12px',
                            padding: '12px 16px',
                            background: '#F9FAFB',
                            borderRadius: '8px',
                          }}
                        >
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="#6B7280"
                            strokeWidth="2"
                            width="20"
                            height="20"
                          >
                            <path
                              d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                            <polyline points="22,6 12,13 2,6"></polyline>
                          </svg>
                          <div style={{flex: 1}}>
                            <div
                              style={{
                                fontSize: '12px',
                                color: '#6B7280',
                                marginBottom: '2px',
                              }}
                            >
                              Your Contact
                            </div>
                            <div
                              style={{
                                fontSize: '15px',
                                color: '#111827',
                                fontWeight: 600,
                              }}
                            >
                              {request.user_contact}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Notes */}
                {request.notes && (
                  <div
                    style={{
                      padding: '16px',
                      background: '#FFFBEB',
                      border: '1px solid #FDE68A',
                      borderRadius: '8px',
                      marginBottom: '20px',
                    }}
                  >
                    <div style={{display: 'flex', gap: '8px'}}>
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
                            marginBottom: '4px',
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
                          {request.notes}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Description */}
                {selectedBooking.description && (
                  <div
                    style={{
                      padding: '16px',
                      background: '#F9FAFB',
                      borderRadius: '8px',
                      marginBottom: '20px',
                    }}
                  >
                    <p
                      style={{
                        fontSize: '14px',
                        lineHeight: '1.6',
                        color: '#374151',
                        margin: 0,
                      }}
                    >
                      {selectedBooking.description}
                    </p>
                  </div>
                )}

                {/* Confirmation Code */}
                {selectedBooking.confirmation_code &&
                  status === 'confirmed' && (
                    <div
                      style={{
                        background:
                          'linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%)',
                        border: '2px solid #10B981',
                        borderRadius: '12px',
                        padding: '20px',
                        marginBottom: '20px',
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
                            background: '#10B981',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                          }}
                        >
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="white"
                            strokeWidth="3"
                            width="28"
                            height="28"
                          >
                            <polyline points="20 6 9 17 4 12"></polyline>
                          </svg>
                        </div>
                        <div style={{flex: 1}}>
                          <div
                            style={{
                              fontSize: '12px',
                              color: '#065F46',
                              fontWeight: 600,
                              marginBottom: '4px',
                              textTransform: 'uppercase',
                              letterSpacing: '0.5px',
                            }}
                          >
                            Confirmation Code
                          </div>
                          <div
                            style={{
                              fontSize: '24px',
                              fontWeight: 700,
                              color: '#065F46',
                              letterSpacing: '3px',
                              fontFamily: 'monospace',
                            }}
                          >
                            {selectedBooking.confirmation_code}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                {/* Error Message */}
                {selectedBooking.error_message && (
                  <div
                    style={{
                      background:
                        'linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%)',
                      border: '2px solid #EF4444',
                      borderRadius: '12px',
                      padding: '20px',
                      marginBottom: '20px',
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
                        }}
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="white"
                          strokeWidth="2"
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
                          Error
                        </div>
                        <div
                          style={{
                            fontSize: '14px',
                            color: '#991B1B',
                            lineHeight: '1.5',
                          }}
                        >
                          {selectedBooking.error_message}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Timestamps */}
                {(selectedBooking.created_at ||
                  selectedBooking.confirmed_time) && (
                  <div
                    style={{
                      display: 'flex',
                      gap: '16px',
                      paddingTop: '16px',
                      borderTop: '1px solid #E5E7EB',
                    }}
                  >
                    {selectedBooking.created_at && (
                      <div style={{flex: 1}}>
                        <div
                          style={{
                            fontSize: '11px',
                            color: '#9CA3AF',
                            marginBottom: '4px',
                            textTransform: 'uppercase',
                            letterSpacing: '0.5px',
                          }}
                        >
                          Created
                        </div>
                        <div
                          style={{
                            fontSize: '13px',
                            color: '#6B7280',
                            fontWeight: 500,
                          }}
                        >
                          {new Date(
                            selectedBooking.created_at,
                          ).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            hour: 'numeric',
                            minute: '2-digit',
                          })}
                        </div>
                      </div>
                    )}
                    {selectedBooking.confirmed_time && (
                      <div style={{flex: 1}}>
                        <div
                          style={{
                            fontSize: '11px',
                            color: '#9CA3AF',
                            marginBottom: '4px',
                            textTransform: 'uppercase',
                            letterSpacing: '0.5px',
                          }}
                        >
                          Confirmed
                        </div>
                        <div
                          style={{
                            fontSize: '13px',
                            color: '#6B7280',
                            fontWeight: 500,
                          }}
                        >
                          {new Date(
                            selectedBooking.confirmed_time,
                          ).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            hour: 'numeric',
                            minute: '2-digit',
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })()}
      </AppDrawer>
    </BookingCardsContainer>
  );
};

export default BookingCards;
