import type {AuthAction, AuthState, GlobalData, Organization, User,} from '@unpod/constants/types';

export const AUTH_ACTIONS = {
  SET_AUTH_USER: 'SET_AUTH_USER',
  UPDATE_AUTH_USER: 'UPDATE_AUTH_USER',
  UPDATE_AUTH_LOADING: 'UPDATE_AUTH_LOADING',
  UPDATE_ACTIVE_ORGANIZATION: 'UPDATE_ACTIVE_ORGANIZATION',
  LOGOUT_AUTH_USER: 'LOGOUT_AUTH_USER',
  SET_VISITOR_ID: 'SET_VISITOR_ID',
  UPDATE_GLOBAL_DATA: 'UPDATE_GLOBAL_DATA',
} as const;

export function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case AUTH_ACTIONS.SET_AUTH_USER: {
      const user = action.payload as User | null;
      return {
        ...state,
        user,
        activeOrg: user?.active_organization || null,
        isAuthenticated: !!user,
      };
    }

    case AUTH_ACTIONS.UPDATE_AUTH_USER: {
      const user = action.payload as User | null;
      return {
        ...state,
        user,
        activeOrg: user?.active_organization || null,
        isAuthenticated: !!user,
      };
    }

    case AUTH_ACTIONS.UPDATE_ACTIVE_ORGANIZATION: {
      return {
        ...state,
        activeOrg: action.payload as Organization | null,
      };
    }

    case AUTH_ACTIONS.LOGOUT_AUTH_USER: {
      return {
        ...state,
        user: null,
        activeOrg: null,
        isAuthenticated: false,
      };
    }

    case AUTH_ACTIONS.UPDATE_AUTH_LOADING: {
      return {
        ...state,
        isLoading: action.payload as boolean,
      };
    }

    case AUTH_ACTIONS.SET_VISITOR_ID: {
      return {
        ...state,
        visitorId: action.payload as string | null,
      };
    }

    case AUTH_ACTIONS.UPDATE_GLOBAL_DATA: {
      return {
        ...state,
        globalData: action.payload as GlobalData,
      };
    }
    default:
      return state;
  }
}
