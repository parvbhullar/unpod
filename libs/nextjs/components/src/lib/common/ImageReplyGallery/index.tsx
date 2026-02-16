import React, { useMemo, useRef, useState } from 'react';
import { useWindowSize } from 'react-use';
import AppImage from '../../next/AppImage';
import {
  StyledActionsWrapper,
  StyledGalleryItem,
  StyledRoot,
} from './index.styled';
import { MdOutlineDownloadForOffline } from 'react-icons/md';
import { Image as AntImage } from 'antd';

type ImageItem = {
  media_url: string;};

type ImageReplyGalleryProps = {
  images: ImageItem[];
  onDownload?: (item: ImageItem, event: React.MouseEvent<SVGElement>) => void;};

const ImageGallery: React.FC<ImageReplyGalleryProps> = ({
  images,
  onDownload,
}) => {
  const { width, height } = useWindowSize();
  const [open, setOpen] = useState(false);
  const [currentItem, setCurrentItem] = useState<ImageItem | null>(null);
  const galleryRef = useRef<HTMLDivElement>(null);

  const { thWidth, thHeight } = useMemo(() => {
    const galleryWidth = (galleryRef.current?.clientWidth ?? 0) - 24;
    return {
      thWidth: galleryWidth ? galleryWidth / 3 : 0,
      thHeight: galleryWidth ? galleryWidth / 3 : 0,
    };
  }, [width, height]);

  const onClick = (item: ImageItem) => {
    setCurrentItem(item);
    setOpen(true);
  };

  console.log(
    'ImageReplyGallery: ',
    galleryRef.current,
    galleryRef.current?.clientWidth,
    images,
    thWidth,
    thHeight,
  );

  return (
    <StyledRoot ref={galleryRef}>
      {images.map((item, index) => (
        <StyledGalleryItem
          key={index}
          style={{
            width: thWidth,
            height: thHeight,
          }}
        >
          <AppImage
            src={`${item.media_url}?tr=h-${thHeight},w-${thWidth}}`}
            alt="Cover Image"
            layout="fill"
            objectFit="cover"
            onClick={() => onClick(item)}
          />
          {onDownload && (
            <StyledActionsWrapper>
              <MdOutlineDownloadForOffline
                fontSize={24}
                className="download-btn"
                onClick={(event) => onDownload(item, event)}
              />
            </StyledActionsWrapper>
          )}
        </StyledGalleryItem>
      ))}

      {currentItem && (
        <AntImage
          style={{ display: 'none' }}
          src={`${currentItem.media_url}?tr=w-1080,h-180`}
          preview={{
            visible: open,
            scaleStep: 0.5,
            src: currentItem.media_url,
            onVisibleChange: setOpen,
          }}
        />
      )}
    </StyledRoot>
  );
};

export default ImageGallery;
