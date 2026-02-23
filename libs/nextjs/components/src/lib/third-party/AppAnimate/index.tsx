import React, {CSSProperties, memo, ReactElement} from 'react';
import {VelocityComponent, VelocityComponentProps} from 'velocity-react';
import 'velocity-animate/velocity.ui';

type AppAnimateProps = VelocityComponentProps & {
  children: ReactElement;
};

const AppAnimate: React.FC<AppAnimateProps> = ({
                                                 children: rawChildren,
                                                 animation = 'transition.fadeIn',
                                                 runOnMount = true,
                                                 targetQuerySelector = null,
                                                 interruptBehavior = 'stop',
                                                 visibility = 'visible',
                                                 duration = 400,
                                                 delay = 100,
                                                 easing = [0.4, 0.0, 0.2, 1],
                                                 display = null,
                                                 setRef = undefined,
                                                 queue = '',
                                                 begin = undefined,
                                                 progress = undefined,
                                                 complete = undefined,
                                                 loop = false,
                                                 mobileHA = true,
                                                 ...restProps
                                               }) => {
  const child = rawChildren as React.ReactElement<{ style?: CSSProperties }>;

  const children = React.cloneElement(child, {
    style: {
      ...(child.props.style || {}),
      visibility: 'hidden',
    },
  });
  return (
    <VelocityComponent
      animation={animation}
      runOnMount={runOnMount}
      targetQuerySelector={targetQuerySelector}
      interruptBehavior={interruptBehavior}
      visibility={visibility}
      duration={duration}
      delay={delay}
      easing={easing}
      display={display}
      setRef={setRef}
      queue={queue}
      begin={begin}
      progress={progress}
      complete={complete}
      loop={loop}
      mobileHA={mobileHA}
      {...restProps}
    >
      {children}
    </VelocityComponent>
  );
};

export default memo(AppAnimate);
