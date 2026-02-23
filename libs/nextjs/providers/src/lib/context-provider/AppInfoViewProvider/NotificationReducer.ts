import type {InfoViewAction, InfoViewState} from '@unpod/constants/types';

export const InfoViewActions = {
  FETCH_STARTS: 'FETCH_STARTS',
  FETCH_SUCCESS: 'FETCH_SUCCESS',
  SET_NOTIFICATION: 'SET_NOTIFICATION',
  SET_ERROR: 'SET_ERROR',
  CLEAR_ALL: 'CLEAR_ALL',
} as const;

export function contextReducer(
  state: InfoViewState,
  action: InfoViewAction,
): InfoViewState {
  switch (action.type) {
    case InfoViewActions.FETCH_STARTS: {
      return {
        ...state,
        loading: true,
        notification: '',
        error: '',
      };
    }
    case InfoViewActions.FETCH_SUCCESS: {
      return {
        ...state,
        loading: false,
        notification: '',
        error: '',
      };
    }
    case InfoViewActions.SET_NOTIFICATION: {
      return {
        ...state,
        loading: false,
        notification: action.payload || '',
        error: '',
      };
    }
    case InfoViewActions.SET_ERROR: {
      return {
        ...state,
        loading: false,
        notification: '',
        error: action.payload || '',
      };
    }
    case InfoViewActions.CLEAR_ALL: {
      return {
        ...state,
        loading: false,
        notification: '',
        error: '',
      };
    }
    default:
      return state;
  }
}
