'use client';
import type {SyntheticEvent} from 'react';
import {useState} from 'react';

import {AppDrawer} from '@unpod/components/antd';
import {
  PersonAvatar,
  PersonCard,
  PersonCardBody,
  PersonCardHeader,
  PersonCardsContainer,
  PersonCardsScroll,
  PersonDescription,
  PersonInfo,
  PersonName,
  PersonQueryHeader,
  PersonScore,
  PersonSocialLink,
  PersonSocialLinks,
  PersonTitleCompany,
} from './index.styled';
import CardsScrollWrapper from './CardsScrollWrapper';

type PersonItem = {
  id?: string | number;
  name?: string;
  image?: string;
  title?: string;
  company?: string;
  score?: number;
  description?: string;
  linkedin_url?: string;
  twitter_url?: string;
  url?: string;
};

type PersonCardsData = {
  items?: PersonItem[];
  query?: string;
};

type PersonCardsProps = {
  data?: PersonCardsData;
};

const PersonCards = ({data}: PersonCardsProps) => {
  const people = data?.items || [];
  const query = data?.query;
  const [selectedPerson, setSelectedPerson] = useState<PersonItem | null>(null);

  return (
    <PersonCardsContainer>
      {query && <PersonQueryHeader>Results for "{query}"</PersonQueryHeader>}
      <CardsScrollWrapper ScrollComponent={PersonCardsScroll} items={people}>
        {people.map((person, index) => (
          <PersonCard
            key={person.id || index}
            onClick={() => setSelectedPerson(person)}
          >
            <PersonCardHeader>
              {person.image && (
                <PersonAvatar
                  src={person.image}
                  alt={person.name}
                  onError={(e: SyntheticEvent<HTMLImageElement>) => {
                    e.currentTarget.style.display = 'none';
                  }}
                />
              )}
              <PersonInfo>
                <PersonName>{person.name}</PersonName>
                {(person.title || person.company) && (
                  <PersonTitleCompany>
                    {person.title}
                    {person.title && person.company && ' at '}
                    {person.company}
                  </PersonTitleCompany>
                )}
                {person.score && (
                  <PersonScore>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="currentColor"
                    >
                      <polygon
                        points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                    </svg>
                    {(person.score * 100).toFixed(0)}% match
                  </PersonScore>
                )}
              </PersonInfo>
            </PersonCardHeader>

            <PersonCardBody>
              {person.description && (
                <PersonDescription>{person.description}</PersonDescription>
              )}

              {(person.linkedin_url || person.twitter_url) && (
                <PersonSocialLinks>
                  {person.linkedin_url && (
                    <PersonSocialLink
                      href={person.linkedin_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 24 24"
                        fill="currentColor"
                      >
                        <path
                          d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                      </svg>
                      LinkedIn
                    </PersonSocialLink>
                  )}
                  {person.twitter_url && (
                    <PersonSocialLink
                      href={person.twitter_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 24 24"
                        fill="currentColor"
                      >
                        <path
                          d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
                      </svg>
                      Twitter
                    </PersonSocialLink>
                  )}
                </PersonSocialLinks>
              )}
            </PersonCardBody>
          </PersonCard>
        ))}
      </CardsScrollWrapper>

      {/* Detail Drawer */}
      <AppDrawer
        open={!!selectedPerson}
        onClose={() => setSelectedPerson(null)}
        title={selectedPerson?.name}
        closable
        placement="right"
        width={550}
      >
        {selectedPerson && (
          <div>
            {selectedPerson.image && (
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'center',
                  marginBottom: '20px',
                }}
              >
                <img
                  src={selectedPerson.image}
                  alt={selectedPerson.name}
                  style={{
                    width: '150px',
                    height: '150px',
                    objectFit: 'cover',
                    borderRadius: '50%',
                    border: '4px solid #4F46E5',
                  }}
                />
              </div>
            )}

            {(selectedPerson.title || selectedPerson.company) && (
              <p
                style={{
                  fontSize: '16px',
                  color: '#666',
                  marginBottom: '16px',
                  textAlign: 'center',
                  fontWeight: 500,
                }}
              >
                {selectedPerson.title}
                {selectedPerson.title && selectedPerson.company && ' at '}
                {selectedPerson.company}
              </p>
            )}

            {selectedPerson.score && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  marginBottom: '20px',
                }}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="#FFD700"
                  width="20"
                  height="20"
                >
                  <polygon
                    points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                </svg>
                <span
                  style={{
                    fontSize: '16px',
                    fontWeight: 600,
                    color: '#4F46E5',
                  }}
                >
                  {(selectedPerson.score * 100).toFixed(0)}% match
                </span>
              </div>
            )}

            {selectedPerson.description && (
              <p
                style={{
                  fontSize: '15px',
                  lineHeight: '1.6',
                  marginBottom: '20px',
                }}
              >
                {selectedPerson.description}
              </p>
            )}

            {(selectedPerson.linkedin_url ||
              selectedPerson.twitter_url ||
              selectedPerson.url) && (
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                  marginTop: '24px',
                }}
              >
                {selectedPerson.linkedin_url && (
                  <a
                    href={selectedPerson.linkedin_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '12px 20px',
                      background: '#0077B5',
                      color: 'white',
                      borderRadius: '8px',
                      textDecoration: 'none',
                      fontWeight: 600,
                    }}
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="currentColor"
                      width="20"
                      height="20"
                    >
                      <path
                        d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                    </svg>
                    View LinkedIn Profile
                  </a>
                )}

                {selectedPerson.twitter_url && (
                  <a
                    href={selectedPerson.twitter_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '12px 20px',
                      background: '#1DA1F2',
                      color: 'white',
                      borderRadius: '8px',
                      textDecoration: 'none',
                      fontWeight: 600,
                    }}
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="currentColor"
                      width="20"
                      height="20"
                    >
                      <path
                        d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
                    </svg>
                    View Twitter Profile
                  </a>
                )}

                {selectedPerson.url && (
                  <a
                    href={selectedPerson.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '12px 20px',
                      background: '#4F46E5',
                      color: 'white',
                      borderRadius: '8px',
                      textDecoration: 'none',
                      fontWeight: 600,
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
                      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                      <polyline points="15 3 21 3 21 9"></polyline>
                      <line x1="10" y1="14" x2="21" y2="3"></line>
                    </svg>
                    Visit Profile →
                  </a>
                )}
              </div>
            )}
          </div>
        )}
      </AppDrawer>
    </PersonCardsContainer>
  );
};

export default PersonCards;
