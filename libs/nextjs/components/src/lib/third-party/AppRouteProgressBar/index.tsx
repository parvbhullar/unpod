'use client';
import {useEffect, useState} from 'react';
import {useRouter} from 'next/router';
import TopBarProgress from 'react-topbar-progress-indicator';


const AppRouteProgressBar = () => {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const routeChangeStart = () => {
      setLoading(true);
    };

    const routeChangeComplete = () => {
      setLoading(false);
    };

    router.events.on('routeChangeStart', routeChangeStart);
    router.events.on('routeChangeComplete', routeChangeComplete);

    return () => {
      router.events.off('routeChangeStart', routeChangeStart);
      router.events.off('routeChangeComplete', routeChangeComplete);
    };
  }, [router.events]);

  return loading && <TopBarProgress/>;
};

export default AppRouteProgressBar;
