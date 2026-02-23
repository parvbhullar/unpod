'use client';
import type {SyntheticEvent} from 'react';
import {useState} from 'react';

import {AppDrawer} from '@unpod/components/antd';
import {
  QueryHeader,
  WebCard,
  WebCardBanner,
  WebCardContent,
  WebCardDate,
  WebCardDescription,
  WebCardDivider,
  WebCardMeta,
  WebCardsContainer,
  WebCardScore,
  WebCardSource,
  WebCardsScroll,
  WebCardTitle,
} from './index.styled';
import CardsScrollWrapper from './CardsScrollWrapper';

type WebItem = {
  id?: string | number;
  name?: string;
  image?: string;
  description?: string;
  source?: string;
  author?: string;
  published_date?: string;
  score?: number;
  url?: string;
};

type WebCardsData = {
  items?: WebItem[];
  query?: string;
};

type WebCardsProps = {
  data?: WebCardsData;
};

const WebCards = ({data}: WebCardsProps) => {
  const webItems = data?.items || [];
  const query = data?.query;
  const [selectedItem, setSelectedItem] = useState<WebItem | null>(null);

  return (
    <WebCardsContainer>
      {query && <QueryHeader>Results for "{query}"</QueryHeader>}
      <CardsScrollWrapper ScrollComponent={WebCardsScroll} items={webItems}>
        {webItems.map((item, index) => (
          <WebCard key={item.id || index} onClick={() => setSelectedItem(item)}>
            {item.image && (
              <WebCardBanner
                src={item.image}
                alt={item.name}
                onError={(e: SyntheticEvent<HTMLImageElement>) => {
                  e.currentTarget.style.display = 'none';
                }}
              />
            )}
            <WebCardContent>
              <WebCardTitle>{item.name}</WebCardTitle>
              {item.description && (
                <WebCardDescription>{item.description}</WebCardDescription>
              )}
              <WebCardMeta>
                {item.source && (
                  <>
                    <WebCardSource>
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        width="12"
                        height="12"
                      >
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="2" y1="12" x2="22" y2="12"></line>
                        <path
                          d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
                      </svg>
                      {item.source}
                    </WebCardSource>
                    {(item.author || item.published_date || item.score) && (
                      <WebCardDivider>•</WebCardDivider>
                    )}
                  </>
                )}
                {item.author && (
                  <>
                    <span>by {item.author}</span>
                    {(item.published_date || item.score) && (
                      <WebCardDivider>•</WebCardDivider>
                    )}
                  </>
                )}
                {item.published_date && (
                  <>
                    <WebCardDate>
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        width="12"
                        height="12"
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
                      {new Date(item.published_date).toLocaleDateString()}
                    </WebCardDate>
                    {item.score && <WebCardDivider>•</WebCardDivider>}
                  </>
                )}
                {item.score && (
                  <WebCardScore>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      width="12"
                      height="12"
                    >
                      <polygon
                        points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                    </svg>
                    {(item.score * 100).toFixed(0)}% match
                  </WebCardScore>
                )}
              </WebCardMeta>
            </WebCardContent>
          </WebCard>
        ))}
      </CardsScrollWrapper>

      {/* Detail Drawer */}
      <AppDrawer
        open={!!selectedItem}
        onClose={() => setSelectedItem(null)}
        title={selectedItem?.name}
        closable
        placement="right"
        width={550}
      >
        {selectedItem && (
          <div>
            {selectedItem.image && (
              <img
                src={selectedItem.image}
                alt={selectedItem.name}
                style={{
                  width: '100%',
                  height: '250px',
                  objectFit: 'cover',
                  borderRadius: '8px',
                  marginBottom: '16px',
                }}
              />
            )}

            {selectedItem.description && (
              <p
                style={{
                  fontSize: '15px',
                  lineHeight: '1.6',
                  marginBottom: '20px',
                }}
              >
                {selectedItem.description}
              </p>
            )}

            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '16px',
                marginBottom: '20px',
              }}
            >
              {selectedItem.source && (
                <div
                  style={{display: 'flex', alignItems: 'center', gap: '8px'}}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    width="16"
                    height="16"
                    style={{flexShrink: 0}}
                  >
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="2" y1="12" x2="22" y2="12"></line>
                    <path
                      d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
                  </svg>
                  <span style={{fontSize: '14px', color: '#666'}}>
                    <strong>Source:</strong> {selectedItem.source}
                  </span>
                </div>
              )}

              {selectedItem.author && (
                <div
                  style={{display: 'flex', alignItems: 'center', gap: '8px'}}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    width="16"
                    height="16"
                    style={{flexShrink: 0}}
                  >
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                  </svg>
                  <span style={{fontSize: '14px', color: '#666'}}>
                    <strong>Author:</strong> {selectedItem.author}
                  </span>
                </div>
              )}

              {selectedItem.published_date && (
                <div
                  style={{display: 'flex', alignItems: 'center', gap: '8px'}}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    width="16"
                    height="16"
                    style={{flexShrink: 0}}
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
                  <span style={{fontSize: '14px', color: '#666'}}>
                    <strong>Published:</strong>{' '}
                    {new Date(selectedItem.published_date).toLocaleDateString(
                      'en-US',
                      {
                        month: 'long',
                        day: 'numeric',
                        year: 'numeric',
                      },
                    )}
                  </span>
                </div>
              )}

              {selectedItem.score && (
                <div
                  style={{display: 'flex', alignItems: 'center', gap: '8px'}}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    width="16"
                    height="16"
                    style={{flexShrink: 0}}
                  >
                    <polygon
                      points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                  </svg>
                  <span style={{fontSize: '14px', color: '#666'}}>
                    <strong>Match Score:</strong>{' '}
                    {(selectedItem.score * 100).toFixed(0)}%
                  </span>
                </div>
              )}
            </div>

            {selectedItem.url && (
              <a
                href={selectedItem.url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: 'inline-block',
                  marginTop: '24px',
                  padding: '12px 24px',
                  background: '#4F46E5',
                  color: 'white',
                  borderRadius: '8px',
                  textDecoration: 'none',
                  fontWeight: 600,
                }}
              >
                Visit Source →
              </a>
            )}
          </div>
        )}
      </AppDrawer>
    </WebCardsContainer>
  );
};

export default WebCards;
