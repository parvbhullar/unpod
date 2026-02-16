import { memo, type ReactNode } from 'react';

import { Carousel, Col, Row } from 'antd';
import { getImageUrl } from '@unpod/helpers/UrlHelper';
import {
  StyledCarouselWrapper,
  StyledImage,
  StyledSliderContent,
  StyledSliderLayoutWrapper,
} from './index.styled';

type SliderLayoutProps = {
  children?: ReactNode;};

const SliderLayout = ({ children }: SliderLayoutProps) => {
  return (
    <StyledSliderLayoutWrapper>
      <Row align={'middle'} className={'h-100'}>
        <Col xs={24} sm={24} md={24} lg={14} xl={14}>
          {children}
        </Col>
        <Col
          xs={24}
          sm={24}
          md={24}
          lg={10}
          xl={10}
          className={'h-100 carousel-col'}
        >
          <StyledCarouselWrapper>
            <Carousel effect="fade" className="auth-slider" autoplay>
              <div>
                <StyledImage
                  src={getImageUrl('slider/slider-1.png')}
                  alt="slider"
                />
                <StyledSliderContent>
                  <h3>
                    “Workspace has saved us thousands of hours of work. We’re
                    able to spin up projects and features faster.”
                  </h3>
                  <h4>Percy Scott</h4>
                  <p>
                    Developer, thinkitive <br />
                    Web design agency
                  </p>
                </StyledSliderContent>
              </div>
              <div>
                <StyledImage
                  src={getImageUrl('slider/slider-2.png')}
                  alt="slider"
                />
                <StyledSliderContent>
                  <h3>
                    “Do the best you can until you know better. Then when you
                    know better, do better.”
                  </h3>
                  <h4>Reginald Padilla</h4>
                  <p>
                    Designer, thinkitive
                    <br />
                    Web design agency
                  </p>
                </StyledSliderContent>
              </div>
              <div>
                <StyledImage
                  src={getImageUrl('slider/slider-3.png')}
                  alt="slider"
                />
                <StyledSliderContent>
                  <h3>
                    “Your income right now is a result of your standards, it is
                    not the industry, it is not the economy.”
                  </h3>
                  <h4>Candice Gross</h4>
                  <p>
                    Developer, thinkitive
                    <br />
                    agency
                  </p>
                </StyledSliderContent>
              </div>
            </Carousel>
          </StyledCarouselWrapper>
        </Col>
      </Row>
    </StyledSliderLayoutWrapper>
  );
};

export default memo(SliderLayout);
