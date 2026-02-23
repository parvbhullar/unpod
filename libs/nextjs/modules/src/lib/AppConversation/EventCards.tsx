'use client';
import type {SyntheticEvent} from 'react';
import {useState} from 'react';
import {Button} from 'antd';
import {ArrowRightOutlined, CalendarOutlined, EnvironmentOutlined, UserOutlined,} from '@ant-design/icons';
import {useIntl} from 'react-intl';

import {AppDrawer} from '@unpod/components/antd';
import {
  EventCard,
  EventCardBanner,
  EventCardContent,
  EventCardDescription,
  EventCardsContainer,
  EventCardsScroll,
  EventCardTitle,
  EventDate,
  EventDetailRow,
  EventDetails,
  EventQueryHeader,
  EventTag,
  EventTags,
} from './index.styled';
import CardsScrollWrapper from './CardsScrollWrapper';

type EventItem = {
  id?: string | number;
  name?: string;
  description?: string;
  image?: string;
  tags?: string[];
  location?: string;
  organizer?: string;
  event_date?: string;
  url?: string;
};

type EventCardsData = {
  items?: EventItem[];
  query?: string;
};

type EventCardsProps = {
  data?: EventCardsData;
};

const EventCards = ({data}: EventCardsProps) => {
  const events = data?.items || [];
  const query = data?.query;
  const [selectedEvent, setSelectedEvent] = useState<EventItem | null>(null);
  const {formatMessage} = useIntl();

  return (
    <EventCardsContainer>
      {query && (
        <EventQueryHeader>
          {formatMessage({id: 'event.resultsFor'})} "{query}"
        </EventQueryHeader>
      )}
      <CardsScrollWrapper ScrollComponent={EventCardsScroll} items={events}>
        {events.map((event, index) => (
          <EventCard
            key={event.id || index}
            onClick={() => setSelectedEvent(event)}
          >
            {event.image && (
              <EventCardBanner
                src={event.image}
                alt={event.name}
                onError={(e: SyntheticEvent<HTMLImageElement>) => {
                  e.currentTarget.style.display = 'none';
                }}
              />
            )}
            <EventCardContent>
              <EventCardTitle>{event.name}</EventCardTitle>
              {event.description && (
                <EventCardDescription>{event.description}</EventCardDescription>
              )}

              {event.tags && event.tags.length > 0 && (
                <EventTags>
                  {event.tags.slice(0, 3).map((tag, tagIndex) => (
                    <EventTag key={tagIndex}>{tag}</EventTag>
                  ))}
                  {event.tags.length > 3 && (
                    <EventTag>+{event.tags.length - 3}</EventTag>
                  )}
                </EventTags>
              )}

              <EventDetails>
                {event.location && (
                  <EventDetailRow>
                    <EnvironmentOutlined/>
                    <span>{event.location}</span>
                  </EventDetailRow>
                )}

                {event.organizer && (
                  <EventDetailRow>
                    <UserOutlined/>
                    <span>
                      {formatMessage({id: 'event.organizedBy'})}{' '}
                      {event.organizer}
                    </span>
                  </EventDetailRow>
                )}
              </EventDetails>

              {event.event_date && (
                <EventDate>
                  <CalendarOutlined/>
                  {new Date(event.event_date).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                  })}{' '}
                  •{' '}
                  {new Date(event.event_date).toLocaleTimeString('en-US', {
                    hour: 'numeric',
                    minute: '2-digit',
                  })}
                </EventDate>
              )}
            </EventCardContent>
          </EventCard>
        ))}
      </CardsScrollWrapper>

      {/* Detail Drawer */}
      <AppDrawer
        open={!!selectedEvent}
        onClose={() => setSelectedEvent(null)}
        title={selectedEvent?.name}
        closable
        placement="right"
        width={550}
      >
        {selectedEvent && (
          <div style={{padding: '4px'}}>
            {selectedEvent.image && (
              <img
                src={selectedEvent.image}
                alt={selectedEvent.name}
                style={{
                  width: '100%',
                  height: '280px',
                  objectFit: 'cover',
                  borderRadius: '12px',
                  marginBottom: '24px',
                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
                }}
              />
            )}

            {selectedEvent.description && (
              <p
                style={{
                  fontSize: '15px',
                  lineHeight: '1.7',
                  marginBottom: '24px',
                  color: 'rgba(0, 0, 0, 0.75)',
                }}
              >
                {selectedEvent.description}
              </p>
            )}

            {selectedEvent.tags && selectedEvent.tags.length > 0 && (
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '8px',
                  marginBottom: '24px',
                }}
              >
                {selectedEvent.tags.map((tag, tagIndex) => (
                  <span
                    key={tagIndex}
                    style={{
                      padding: '8px 16px',
                      background:
                        'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                      color: 'white',
                      borderRadius: '20px',
                      fontSize: '12px',
                      fontWeight: 600,
                      boxShadow: '0 2px 8px rgba(99, 102, 241, 0.3)',
                    }}
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}

            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '16px',
                marginBottom: '28px',
                padding: '20px',
                background: 'rgba(0, 0, 0, 0.02)',
                borderRadius: '12px',
                border: '1px solid rgba(0, 0, 0, 0.08)',
              }}
            >
              {selectedEvent.event_date && (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '12px',
                  }}
                >
                  <CalendarOutlined
                    style={{
                      fontSize: '18px',
                      color: '#6366f1',
                      marginTop: '2px',
                    }}
                  />
                  <div style={{flex: 1}}>
                    <div
                      style={{
                        fontSize: '12px',
                        color: 'rgba(0, 0, 0, 0.5)',
                        marginBottom: '4px',
                        fontWeight: 600,
                        textTransform: 'uppercase',
                      }}
                    >
                      {formatMessage({id: 'event.dateTime'})}
                    </div>
                    <div
                      style={{
                        fontSize: '14px',
                        color: 'rgba(0, 0, 0, 0.85)',
                        fontWeight: 500,
                      }}
                    >
                      {new Date(selectedEvent.event_date).toLocaleDateString(
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
                        fontSize: '13px',
                        color: 'rgba(0, 0, 0, 0.6)',
                        marginTop: '2px',
                      }}
                    >
                      {new Date(selectedEvent.event_date).toLocaleTimeString(
                        'en-US',
                        {
                          hour: 'numeric',
                          minute: '2-digit',
                        },
                      )}
                    </div>
                  </div>
                </div>
              )}

              {selectedEvent.location && (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '12px',
                  }}
                >
                  <EnvironmentOutlined
                    style={{
                      fontSize: '18px',
                      color: '#10b981',
                      marginTop: '2px',
                    }}
                  />
                  <div style={{flex: 1}}>
                    <div
                      style={{
                        fontSize: '12px',
                        color: 'rgba(0, 0, 0, 0.5)',
                        marginBottom: '4px',
                        fontWeight: 600,
                        textTransform: 'uppercase',
                      }}
                    >
                      {formatMessage({id: 'event.location'})}
                    </div>
                    <div
                      style={{
                        fontSize: '14px',
                        color: 'rgba(0, 0, 0, 0.85)',
                        fontWeight: 500,
                      }}
                    >
                      {selectedEvent.location}
                    </div>
                  </div>
                </div>
              )}

              {selectedEvent.organizer && (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '12px',
                  }}
                >
                  <UserOutlined
                    style={{
                      fontSize: '18px',
                      color: '#f59e0b',
                      marginTop: '2px',
                    }}
                  />
                  <div style={{flex: 1}}>
                    <div
                      style={{
                        fontSize: '12px',
                        color: 'rgba(0, 0, 0, 0.5)',
                        marginBottom: '4px',
                        fontWeight: 600,
                        textTransform: 'uppercase',
                      }}
                    >
                      {formatMessage({id: 'event.organizer'})}
                    </div>
                    <div
                      style={{
                        fontSize: '14px',
                        color: 'rgba(0, 0, 0, 0.85)',
                        fontWeight: 500,
                      }}
                    >
                      {selectedEvent.organizer}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {selectedEvent.url && (
              <Button
                type="primary"
                size="large"
                block
                href={selectedEvent.url}
                target="_blank"
                rel="noopener noreferrer"
                icon={<ArrowRightOutlined/>}
                iconPlacement="end"
                style={{
                  height: '48px',
                  fontSize: '15px',
                  fontWeight: 600,
                  borderRadius: '12px',
                  background:
                    'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                  border: 'none',
                  boxShadow: '0 4px 12px rgba(99, 102, 241, 0.4)',
                }}
              >
                {formatMessage({id: 'event.viewDetails'})}
              </Button>
            )}
          </div>
        )}
      </AppDrawer>
    </EventCardsContainer>
  );
};

export default EventCards;
