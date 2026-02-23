import React, {useEffect, useState} from 'react';
import Image, {ImageProps} from 'next/image';

type AppImageProps = Omit<ImageProps, 'src' | 'alt'> & {
  src: string;
  alt?: string;
  layout?: 'fill' | 'fixed' | 'intrinsic' | 'responsive';
  preview?: boolean;
  fallback?: string;
  priority?: boolean;
};

const AppImage: React.FC<AppImageProps> = ({
                                             src,
                                             height,
                                             width,
                                             layout,
                                             alt = 'unpod',
                                             priority = false,
                                             loading,
                                             fallback,
                                             style,
                                             ...props
                                           }) => {
  const [imgSrc, setImgSrc] = useState<string>(src);

  useEffect(() => {
    setImgSrc(src);
  }, [src]);

  // Determine loading strategy - priority images should not have loading="lazy"
  const loadingProp = priority ? undefined : loading || 'lazy';

  // Check if the image is an SVG - SVGs should not be optimized by Next.js
  const isSVG =
    typeof imgSrc === 'string' && imgSrc.toLowerCase().endsWith('.svg');
  const unoptimized = isSVG || props.unoptimized;

  if (!imgSrc) {
    return null;
  }

  const handleError: React.ReactEventHandler<HTMLImageElement> = () => {
    if (fallback && imgSrc !== fallback) {
      setImgSrc(fallback);
      return;
    }
    setImgSrc('');
  };

  if (layout === 'fill') {
    return (
      <Image
        src={imgSrc}
        alt={alt}
        fill
        priority={priority}
        loading={loadingProp}
        unoptimized={unoptimized}
        onError={handleError}
        {...props}
      />
    );
  }
  return (
    <Image
      src={imgSrc}
      height={height}
      width={width}
      alt={alt}
      priority={priority}
      loading={loadingProp}
      unoptimized={unoptimized}
      onError={handleError}
      {...props}
      style={{maxWidth: '100%', height: 'auto', ...style}}
    />
  );
};

export default AppImage;
