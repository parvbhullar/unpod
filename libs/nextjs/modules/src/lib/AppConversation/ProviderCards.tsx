'use client';
import type { SyntheticEvent } from 'react';
import { useState } from 'react';

import { AppDrawer } from '@unpod/components/antd';
import {
  Badge,
  ProviderBadges,
  ProviderCard,
  ProviderCardHeader,
  ProviderCardsContainer,
  ProviderCardsScroll,
  ProviderDescription,
  ProviderDetailRow,
  ProviderDetails,
  ProviderImage,
  ProviderInfo,
  ProviderName,
  ProviderQueryHeader,
  ProviderRating,
  Star,
} from './index.styled';
import CardsScrollWrapper from './CardsScrollWrapper';

type ProviderItem = {
  id?: string | number;
  name?: string;
  image?: string;
  description?: string;
  rating?: number;
  reviews_count?: number;
  address?: string;
  phone?: string;
  opening_hours?: string;
  distance_km?: number;
  is_open?: boolean;
  price_level?: number;
  url?: string;
};

type ProviderCardsData = {
  items?: ProviderItem[];
  query?: string;
};

type ProviderCardsProps = {
  data?: ProviderCardsData;
};

const ProviderCards = ({ data }: ProviderCardsProps) => {
  const providers = data?.items || [];
  const query = data?.query;
  const [selectedProvider, setSelectedProvider] = useState<ProviderItem | null>(
    null,
  );

  return (
    <ProviderCardsContainer>
      {query && (
        <ProviderQueryHeader>Results for "{query}"</ProviderQueryHeader>
      )}
      <CardsScrollWrapper
        ScrollComponent={ProviderCardsScroll}
        items={providers}
      >
        {providers.map((provider, index) => (
          <ProviderCard
            key={provider.id || index}
            onClick={() => setSelectedProvider(provider)}
          >
            <ProviderCardHeader>
              {provider.image && (
                <ProviderImage
                  src={provider.image}
                  alt={provider.name}
                  onError={(e: SyntheticEvent<HTMLImageElement>) => {
                    e.currentTarget.style.display = 'none';
                  }}
                />
              )}
              <ProviderInfo>
                <ProviderName>{provider.name}</ProviderName>
                {provider.description && (
                  <ProviderDescription>
                    {provider.description}
                  </ProviderDescription>
                )}
                {provider.rating && (
                  <ProviderRating>
                    <Star>★</Star>
                    <strong>{provider.rating.toFixed(1)}</strong>
                    {provider.reviews_count && (
                      <span>
                        ({provider.reviews_count.toLocaleString()} reviews)
                      </span>
                    )}
                  </ProviderRating>
                )}
              </ProviderInfo>
            </ProviderCardHeader>

            <ProviderDetails>
              {provider.address && (
                <ProviderDetailRow>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                    <circle cx="12" cy="10" r="3"></circle>
                  </svg>
                  <span>{provider.address}</span>
                </ProviderDetailRow>
              )}

              {provider.phone && (
                <ProviderDetailRow>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
                  </svg>
                  <span>{provider.phone}</span>
                </ProviderDetailRow>
              )}

              {provider.opening_hours && (
                <ProviderDetailRow>
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
                  <span>{provider.opening_hours}</span>
                </ProviderDetailRow>
              )}

              {provider.distance_km !== undefined && (
                <ProviderDetailRow>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <line x1="18" y1="20" x2="18" y2="10"></line>
                    <line x1="12" y1="20" x2="12" y2="4"></line>
                    <line x1="6" y1="20" x2="6" y2="14"></line>
                  </svg>
                  <span>{provider.distance_km} km away</span>
                </ProviderDetailRow>
              )}
            </ProviderDetails>

            <ProviderBadges>
              {provider.is_open !== undefined && (
                <Badge $variant={provider.is_open ? 'success' : 'warning'}>
                  {provider.is_open ? 'Open Now' : 'Closed'}
                </Badge>
              )}
              {provider.price_level && (
                <Badge>{'$'.repeat(provider.price_level)}</Badge>
              )}
            </ProviderBadges>
          </ProviderCard>
        ))}
      </CardsScrollWrapper>

      {/* Detail Drawer */}
      <AppDrawer
        open={!!selectedProvider}
        onClose={() => setSelectedProvider(null)}
        title={selectedProvider?.name}
        closable
        placement="right"
        width={550}
      >
        {selectedProvider && (
          <div>
            {selectedProvider.image && (
              <img
                src={selectedProvider.image}
                alt={selectedProvider.name}
                style={{
                  width: '100%',
                  height: '250px',
                  objectFit: 'cover',
                  borderRadius: '8px',
                  marginBottom: '16px',
                }}
              />
            )}

            {selectedProvider.description && (
              <p
                style={{
                  fontSize: '15px',
                  lineHeight: '1.6',
                  marginBottom: '20px',
                }}
              >
                {selectedProvider.description}
              </p>
            )}

            {selectedProvider.rating && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  marginBottom: '20px',
                }}
              >
                <Star style={{ fontSize: '20px' }}>★</Star>
                <strong style={{ fontSize: '18px' }}>
                  {selectedProvider.rating.toFixed(1)}
                </strong>
                {selectedProvider.reviews_count && (
                  <span style={{ color: '#666' }}>
                    ({selectedProvider.reviews_count.toLocaleString()} reviews)
                  </span>
                )}
              </div>
            )}

            <div
              style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}
            >
              {selectedProvider.address && (
                <ProviderDetailRow>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                    <circle cx="12" cy="10" r="3"></circle>
                  </svg>
                  <span>{selectedProvider.address}</span>
                </ProviderDetailRow>
              )}

              {selectedProvider.phone && (
                <ProviderDetailRow>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
                  </svg>
                  <a
                    href={`tel:${selectedProvider.phone}`}
                    style={{ color: 'inherit', textDecoration: 'none' }}
                  >
                    {selectedProvider.phone}
                  </a>
                </ProviderDetailRow>
              )}

              {selectedProvider.opening_hours && (
                <ProviderDetailRow>
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
                  <span>{selectedProvider.opening_hours}</span>
                </ProviderDetailRow>
              )}

              {selectedProvider.distance_km !== undefined && (
                <ProviderDetailRow>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <line x1="18" y1="20" x2="18" y2="10"></line>
                    <line x1="12" y1="20" x2="12" y2="4"></line>
                    <line x1="6" y1="20" x2="6" y2="14"></line>
                  </svg>
                  <span>{selectedProvider.distance_km} km away</span>
                </ProviderDetailRow>
              )}
            </div>

            {selectedProvider.url && (
              <a
                href={selectedProvider.url}
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
                Visit Website →
              </a>
            )}
          </div>
        )}
      </AppDrawer>
    </ProviderCardsContainer>
  );
};

export default ProviderCards;
