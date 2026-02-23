import React, {Fragment, useEffect, useMemo, useState} from 'react';
import {Image as AntImage} from 'antd';
import {useWindowSize} from 'react-use';
import AppImage from '../../next/AppImage';
import {StyledActionsWrapper, StyledGalleryItem, StyledRoot,} from './index.styled';
import {MdOutlineDownloadForOffline} from 'react-icons/md';

type Image = {
  media_url: string;
};

type ImageGalleryProps = {
  images: Image[];
  onDownload?: (
    item: Image,
    event: React.MouseEvent<SVGElement, MouseEvent>,
  ) => void;
  style?: React.CSSProperties;
};

const ImageGallery: React.FC<ImageGalleryProps> = ({
                                                     images,
                                                     onDownload,
                                                     ...restProps
                                                   }) => {
  const {width, height} = useWindowSize();
  const [open, setOpen] = useState(false);
  const [currentItem, setCurrentItem] = useState<Image | null>(null);
  const [containerStyle, setContainerStyle] = useState<React.CSSProperties>({
    display: 'block',
  });
  const galleryRef = React.useRef<HTMLDivElement>(null);

  const {thHeight} = useMemo(() => {
    const galleryWidth = (galleryRef.current?.clientWidth ?? 0) - 24;
    return {
      thWidth: galleryWidth ? galleryWidth / 3 : 0,
      thHeight: galleryWidth ? galleryWidth / 3 : 0,
    };
  }, [width, height]);

  useEffect(() => {
    if (images && images.length > 0) {
      if (images.length === 2)
        setContainerStyle({display: 'flex', flexWrap: 'nowrap'});
      else if (images.length > 2)
        setContainerStyle({gridTemplateColumns: `repeat(3, 1fr)`});

      setCurrentItem(images[0]);
    }
  }, [images]);

  return (
    <Fragment>
      <StyledRoot ref={galleryRef} {...restProps} style={containerStyle}>
        {images.map((item, index) => (
          <StyledGalleryItem
            key={index}
            style={{
              // width: thWidth,
              height: images.length > 2 ? thHeight : 'auto',
            }}
            onMouseOver={() => setCurrentItem(item)}
          >
            {images.length > 2 ? (
              <AppImage
                src={`${item.media_url}?tr=h-${thHeight}}`}
                alt="Cover"
                layout="fill"
                objectFit="cover"
                onClick={() => setOpen(true)}
              />
            ) : (
              <img
                className="gallery-thumbnail"
                src={`${item.media_url}?tr=h-${thHeight}`}
                alt="Cover"
                onClick={() => setOpen(true)}
              />
            )}

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
      </StyledRoot>

      {currentItem && (
        <AntImage
          style={{display: 'none'}}
          src={`${currentItem.media_url}?tr=w-1080,h-180`}
          preview={{
            visible: open,
            scaleStep: 0.5,
            src: currentItem.media_url,
            onVisibleChange: setOpen,
          }}
        />
      )}
    </Fragment>
  );
};

export default React.memo(ImageGallery);
