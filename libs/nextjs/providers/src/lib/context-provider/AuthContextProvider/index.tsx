'use client';

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useLayoutEffect,
  useState,
} from 'react';
import {
  httpLocalClient,
  setAuthToken,
  setFirebaseConfig,
  setOrgHeader,
} from '@unpod/services';
import { getDataApi, postDataApi } from '../../APIHooks';
import { useInfoViewActionsContext } from '../AppInfoViewProvider';
import { consoleLog, isEmptyObject } from '@unpod/helpers/GlobalHelper';
import { useRouter } from 'next/navigation';
import { getCurrentBrowserFingerPrint } from '@rajesh896/broprint.js';
import { clearLocalStorage } from '@unpod/helpers/DraftHelper';
import type {
  AuthActionsContextType,
  AuthContextProviderProps,
  AuthState,
  GlobalData,
  Organization,
  User,
} from '@unpod/constants/types';

const ContextState: AuthState = {
  user: null,
  activeOrg: null,
  isAuthenticated: false,
  isLoading: true,
  visitorId: null,
  currency: process.env.currency,
  globalData: {
    permissions: null,
    roles: null,
    profile_roles: null,
  },
};

const AuthContext = createContext<AuthState>(ContextState);
const AuthActionsContext = createContext<AuthActionsContextType | undefined>(
  undefined,
);

export const useAuthContext = (): AuthState => useContext(AuthContext);
export const useAuthActionsContext = (): AuthActionsContextType => {
  const context = useContext(AuthActionsContext);
  if (!context) {
    throw new Error(
      'useAuthActionsContext must be used within AuthContextProvider',
    );
  }
  return context;
};

export const AuthContextProvider: React.FC<AuthContextProviderProps> = (
  props,
) => {
  const router = useRouter();
  const [state, setState] = useState<AuthState>({
    user: props?.userData?.user || null,
    activeOrg: props?.userData?.user?.active_organization || null,
    isAuthenticated: props?.isAuthenticate || false,
    isLoading: !props?.isAuthenticate,
    visitorId: null,
    currency: process.env.currency,
    globalData: {
      permissions: null,
      roles: null,
      profile_roles: null,
    },
  });

  const infoViewActionsContext = useInfoViewActionsContext();

  useLayoutEffect(() => {
    const { isAuthenticate, userData } = props;
    if (isAuthenticate && userData) {
      setAuthToken(userData.token);
      const user = userData.user;
      if (user?.active_organization) {
        setOrgHeader(user?.active_organization.domain_handle);
      }
      if (user) {
        onSuccessAuthenticate(user);
      }
    }
  }, [props.isAuthenticate]);

  const setVisitorId = useCallback((visitorId: string) => {
    setState((prev: AuthState) => ({ ...prev, visitorId }));
  }, []);

  const updateAuthUser = useCallback((user: User | null) => {
    setState((prev: AuthState) => ({
      ...prev,
      user,
      isAuthenticated: !!user,
    }));
  }, []);

  const updateAuthLoading = useCallback((loading: boolean) => {
    setState((prev: AuthState) => ({ ...prev, isLoading: loading }));
  }, []);

  const setActiveOrg = useCallback((org: Organization | null) => {
    setState((prev: AuthState) => ({ ...prev, activeOrg: org }));
  }, []);

  const logoutAuthUser = useCallback(() => {
    setState((prev: AuthState) => ({
      ...prev,
      user: null,
      isAuthenticated: false,
      activeOrg: null,
    }));
  }, []);

  // Check if running in Tauri desktop app
  const isTauri =
    typeof window !== 'undefined' &&
    ('__TAURI__' in window || '__TAURI_INTERNALS__' in window);

  const getToken = useCallback(async (): Promise<{
    data: { token?: string };
  }> => {
    // Use Tauri's persistent storage if available
    if (isTauri) {
      try {
        const { invoke } = await import('@tauri-apps/api/core');
        const token = await invoke<string>('session_get_token');
        return { data: { token } };
      } catch (error) {
        console.error('Failed to get token from Tauri:', error);
      }
    }
    return httpLocalClient.get('/api/token/');
  }, [isTauri]);

  const storeToken = useCallback(
    async (token: string): Promise<unknown> => {
      // Store in Tauri's persistent storage if available
      if (isTauri) {
        try {
          const { invoke } = await import('@tauri-apps/api/core');
          await invoke('session_set_token', { token });
          // Also store in cookie as fallback
          return httpLocalClient.post('/api/token/', { token });
        } catch (error) {
          console.error('Failed to store token in Tauri:', error);
        }
      }
      return httpLocalClient.post('/api/token/', { token });
    },
    [isTauri],
  );

  const deleteToken = useCallback(async (): Promise<unknown> => {
    clearLocalStorage();
    // Delete from Tauri's persistent storage if available
    if (isTauri) {
      try {
        const { invoke } = await import('@tauri-apps/api/core');
        await invoke('session_delete_token');
      } catch (error) {
        console.error('Failed to delete token from Tauri:', error);
      }
    }
    return httpLocalClient.delete('/api/token/');
  }, [isTauri]);

  const updateGlobalData = useCallback((data: GlobalData) => {
    setState((prev: AuthState) => ({ ...prev, globalData: data }));
  }, []);

  const getGlobalData = useCallback((): Promise<unknown> => {
    return new Promise((resolve, reject) => {
      getDataApi<GlobalData>('core/basic-settings/', infoViewActionsContext)
        .then((res) => {
          updateGlobalData(res.data);
          return resolve(res);
        })
        .catch((response: { message: string }) => {
          infoViewActionsContext.showError(response.message);
          return reject(response);
        });
    });
  }, [infoViewActionsContext, updateGlobalData]);

  useEffect(() => {
    if (state.activeOrg?.domain_handle) {
      getDataApi<Organization>(
        `organization/detail/${state.activeOrg?.domain_handle}/`,
        infoViewActionsContext,
        {},
      ).then((res) => {
        setActiveOrg(res.data);
      });
    }
  }, [state.activeOrg?.domain_handle]);

 const getAuthUser = useCallback((): Promise<unknown> => {
    return new Promise((resolve, reject) => {
      getDataApi<User>('auth/me/', infoViewActionsContext)
        .then((res) => {
          updateAuthUser(res.data);
          return resolve(res);
        })
        .catch((response: unknown) => {
          setAuthToken(null);
          return reject(response);
        });
    });
  }, [infoViewActionsContext, updateAuthUser]);

  const signUpUser = useCallback(
    (payload: unknown): Promise<unknown> => {
      return new Promise((resolve, reject) => {
        postDataApi<unknown>('auth/register/', infoViewActionsContext, payload)
          .then((response) => {
            return resolve(response);
          })
          .catch((response: unknown) => {
            return reject(response);
          });
      });
    },
    [infoViewActionsContext],
  );

  const signInUser = useCallback(
    (payload: unknown): Promise<unknown> => {
      return new Promise((resolve, reject) => {
        postDataApi<{ token: string; user: User }>(
          'auth/login/',
          infoViewActionsContext,
          payload,
        )
          .then((res) => {
            storeToken(res.data.token)
              .then(() => {
                setAuthToken(res.data.token);
                getDataApi<User>('auth/me/', infoViewActionsContext)
                  .then((meRes) => {
                    if (meRes.data?.active_organization?.domain_handle) {
                      setOrgHeader(
                        meRes.data.active_organization.domain_handle,
                      );
                      setActiveOrg(meRes.data.active_organization);
                    }

                    updateAuthUser(meRes.data);
                    return resolve({ ...meRes, token: res.data.token });
                  })
                  .catch((response: unknown) => {
                    return reject(response);
                  });
              })
              .catch((response: unknown) => {
                return reject(response);
              });
          })
          .catch((response: unknown) => {
            return reject(response);
          });
      });
    },
    [
      infoViewActionsContext,
      storeToken,
      setActiveOrg,
      updateAuthUser,
    ],
  );

  const logoutUser = useCallback((): Promise<unknown> => {
    return new Promise((resolve, reject) => {
      getDataApi('auth/logout/', infoViewActionsContext)
        .then((response: unknown) => {
          deleteToken()
            .then(() => {
              setAuthToken(null);
              logoutAuthUser();
              return resolve(response);
            })
            .catch((response: unknown) => {
              return reject(response);
            });
        })
        .catch((response: unknown) => {
          return reject(response);
        });
    });
  }, [infoViewActionsContext, deleteToken, logoutAuthUser]);

  const onSuccessAuthenticate = (user: User): void => {
    getGlobalData()
      .then(() => {
        updateAuthUser(user);
        updateAuthLoading(false);

        if (user?.current_step !== 'completed') {
          if (
            user?.current_step === 'join_organization' ||
            user?.current_step === 'organization'
          ) {
            if (isEmptyObject(user?.organization || {})) {
              if (user?.is_private_domain) {
                router.push('/creating-identity/');
              } else {
                router.push('/business-identity/');
              }
            } else {
              router.push('/join-org');
            }
          } else if (user?.current_step === 'profile') {
            router.push('/basic-profile');
          } else router.push(`/${user?.current_step}`);
        }
      })
      .catch((response: unknown) => {
        consoleLog('getGlobalData error', response);
      });
  };

  useEffect(() => {
    getCurrentBrowserFingerPrint()
      .then((fingerprint: unknown) => {
        setVisitorId(String(fingerprint));

        const apiKey = process.env.FIREBASE_API_KEY;
        const projectId = process.env.FIREBASE_PROJECT_ID;
        const messagingSenderId =
          process.env.FIREBASE_MESSAGING_SENDER_ID;
        const appId = process.env.FIREBASE_APP_ID;
        const measurementId = process.env.FIREBASE_MEASUREMENT_ID;
        const authDomain =
          process.env.FIREBASE_AUTH_DOMAIN ||
          (projectId ? `${projectId}.firebaseapp.com` : undefined);
        const storageBucket =
          process.env.FIREBASE_STORAGE_BUCKET ||
          (projectId ? `${projectId}.appspot.com` : undefined);

        const missing: string[] = [];
        if (!apiKey) missing.push('FIREBASE_API_KEY');
        if (!projectId) missing.push('FIREBASE_PROJECT_ID');
        if (!messagingSenderId)
          missing.push('FIREBASE_MESSAGING_SENDER_ID');
        if (!appId) missing.push('FIREBASE_APP_ID');
        if (!measurementId)
          missing.push('FIREBASE_MEASUREMENT_ID');

        if (missing.length > 0) {
          console.warn(
            `[AuthContextProvider] Missing Firebase env vars: ${missing.join(
              ', ',
            )}. Firebase auth will be disabled.`,
          );
          return;
        }

        setFirebaseConfig({
          apiKey,
          authDomain,
          projectId,
          storageBucket,
          messagingSenderId,
          appId,
          measurementId,
        });

        getToken()
          .then((tokenRes) => {
            if (tokenRes.data?.token) {
              setAuthToken(tokenRes.data.token);

              getDataApi<User>('auth/me/', infoViewActionsContext)
                .then((meRes) => {
                  if (meRes.data?.active_organization?.domain_handle) {
                    setOrgHeader(meRes.data.active_organization.domain_handle);
                  }
                  onSuccessAuthenticate(meRes.data);
                })
                .catch(() => {
                  deleteToken()
                    .then(() => {
                      setAuthToken(null);
                      updateAuthLoading(false);
                    })
                    .catch(() => {
                      updateAuthLoading(false);
                    });
                });
            } else {
              updateAuthLoading(false);
            }
          })
          .catch(() => {
            clearLocalStorage();
            updateAuthLoading(false);
          });
      })
      .catch((error: unknown) => {
        console.info('Fingerprint Error', error);
      });
  }, []);

  const authActions = React.useMemo<AuthActionsContextType>(
    () => ({
      onSuccessAuthenticate,
      storeToken,
      setActiveOrg,
      getAuthUser,
      updateAuthUser,
      signInUser,
      signUpUser,
      logoutUser,
      getGlobalData,
    }),
    [
      storeToken,
      setActiveOrg,
      getAuthUser,
      updateAuthUser,
      signInUser,
      signUpUser,
      logoutUser,
      getGlobalData,
    ],
  );

  return (
    <AuthActionsContext.Provider value={authActions}>
      <AuthContext.Provider value={state}>
        {props.children}
      </AuthContext.Provider>
    </AuthActionsContext.Provider>
  );
};

export default AuthContextProvider;
