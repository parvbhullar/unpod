'use client';

import {
  StyledGlow,
  StyledOrbit,
  StyledOrbitContainer,
  StyledOrbitDot,
  StyledOrbitLogo,
  StyledOrbitWrapper,
  StyledUnpodLogo,
} from './index.styled';

const UnpodLogoAnimation = ({
  size = 320,
  showOrbits = true,
  showGlow = true,
  orbitSpeed = 1,
}) => {
  return (
    <StyledOrbitContainer size={size}>
      {showGlow && <StyledGlow size={size} />}

      {showOrbits && (
        <StyledOrbitWrapper size={size}>
          <StyledOrbit duration={3 / orbitSpeed}>
            <StyledOrbitDot
              dotSize={12}
              gradient="linear-gradient(135deg, #5046e5, #818cf8)"
            />
          </StyledOrbit>
          <StyledOrbit duration={4 / orbitSpeed} $reverse>
            <StyledOrbitDot
              dotSize={9}
              gradient="linear-gradient(135deg, #6366f1, #a5b4fc)"
            />
          </StyledOrbit>
          <StyledOrbit duration={5 / orbitSpeed}>
            <StyledOrbitDot
              dotSize={7}
              gradient="linear-gradient(135deg, #818cf8, #c7d2fe)"
            />
          </StyledOrbit>
        </StyledOrbitWrapper>
      )}

      <StyledOrbitLogo size={size}>
        <StyledUnpodLogo
          viewBox="0 0 200 220"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* SVG Definitions for gradients and effects */}
          <defs>
            {/* Radial gradient for iris - Tech/AI theme (Electric Blue) */}
            <radialGradient id="irisGradient" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#6366f1" stopOpacity="1" />
              <stop offset="50%" stopColor="#5046e5" stopOpacity="1" />
              <stop offset="100%" stopColor="#4338ca" stopOpacity="1" />
            </radialGradient>

            {/* Clip paths to keep pupil within iris boundaries */}
            <clipPath id="leftEyeClip">
              <circle cx="75" cy="127" r="9.5" />
            </clipPath>
            <clipPath id="rightEyeClip">
              <circle cx="125" cy="127" r="9.5" />
            </clipPath>

            {/* Clip paths for ear sound waves - show only outer side (away from head) */}
            <clipPath id="leftEarWaveClip">
              <rect x="0" y="80" width="25" height="100" />
            </clipPath>
            <clipPath id="rightEarWaveClip">
              <rect x="175" y="80" width="50" height="100" />
            </clipPath>
          </defs>

          {/* Antenna base - with gap above head */}
          <ellipse className="body" cx="100" cy="70" rx="25" ry="6" />

          {/* Antenna */}
          <line
            x1="100"
            y1="64"
            x2="100"
            y2="40"
            stroke="#5046e5"
            strokeWidth="6"
            strokeLinecap="round"
          />
          <circle className="antenna-ball" cx="100" cy="40" r="8" />

          {/* Main head/body */}
          <path
            className="body"
            d="M 30 100 C 30 60, 170 60, 170 100 L 170 150 C 170 190, 30 190, 30 150 Z"
          />

          {/* LEFT EAR - Tech/Robot style with anatomical structure */}
          <g className="left-ear">
            {/* 1. Outer ear casing - Main visible structure */}
            <ellipse
              className="ear-outer"
              cx="25"
              cy="130"
              rx="18"
              ry="25"
              fill="#5046e5"
            />

            {/* 2. Speaker grill lines - Tech aesthetic (lighter than main color) */}
            <g className="speaker-grill" opacity="0.3">
              <line
                x1="17"
                y1="120"
                x2="33"
                y2="120"
                stroke="#FFFFFF"
                strokeWidth="1"
                strokeLinecap="round"
              />
              <line
                x1="17"
                y1="125"
                x2="33"
                y2="125"
                stroke="#FFFFFF"
                strokeWidth="1"
                strokeLinecap="round"
              />
              <line
                x1="17"
                y1="130"
                x2="33"
                y2="130"
                stroke="#FFFFFF"
                strokeWidth="1"
                strokeLinecap="round"
              />
              <line
                x1="17"
                y1="135"
                x2="33"
                y2="135"
                stroke="#FFFFFF"
                strokeWidth="1"
                strokeLinecap="round"
              />
              <line
                x1="17"
                y1="140"
                x2="33"
                y2="140"
                stroke="#FFFFFF"
                strokeWidth="1"
                strokeLinecap="round"
              />
            </g>

            {/* 3. Sound wave indicators - White color for animation (outer side only) */}
            <g clipPath="url(#leftEarWaveClip)">
              <circle
                className="sound-wave-1"
                cx="25"
                cy="130"
                r="12"
                fill="none"
                stroke="#FFFFFF"
                strokeWidth="1.5"
                opacity="0"
              />
              <circle
                className="sound-wave-2"
                cx="25"
                cy="130"
                r="16"
                fill="none"
                stroke="#FFFFFF"
                strokeWidth="1.5"
                opacity="0"
              />
              <circle
                className="sound-wave-3"
                cx="25"
                cy="130"
                r="20"
                fill="none"
                stroke="#FFFFFF"
                strokeWidth="1.5"
                opacity="0"
              />
            </g>

            {/* 5. LED indicator - Tech detail */}
            <circle
              className="ear-led"
              cx="25"
              cy="108"
              r="2"
              fill="#5046e5"
              opacity="0.8"
            />

            {/* 6. Highlight for depth and dimension */}
            <ellipse
              className="ear-highlight"
              cx="20"
              cy="120"
              rx="4"
              ry="7"
              fill="#FFFFFF"
              opacity="0.4"
            />
          </g>

          {/* RIGHT EAR - Tech/Robot style with anatomical structure */}
          <g className="right-ear">
            {/* 1. Outer ear casing - Main visible structure */}
            <ellipse
              className="ear-outer"
              cx="175"
              cy="130"
              rx="18"
              ry="25"
              fill="#5046e5"
            />

            {/* 2. Speaker grill lines - Tech aesthetic (lighter than main color) */}
            <g className="speaker-grill" opacity="0.3">
              <line
                x1="167"
                y1="120"
                x2="183"
                y2="120"
                stroke="#FFFFFF"
                strokeWidth="1"
                strokeLinecap="round"
              />
              <line
                x1="167"
                y1="125"
                x2="183"
                y2="125"
                stroke="#FFFFFF"
                strokeWidth="1"
                strokeLinecap="round"
              />
              <line
                x1="167"
                y1="130"
                x2="183"
                y2="130"
                stroke="#FFFFFF"
                strokeWidth="1"
                strokeLinecap="round"
              />
              <line
                x1="167"
                y1="135"
                x2="183"
                y2="135"
                stroke="#FFFFFF"
                strokeWidth="1"
                strokeLinecap="round"
              />
              <line
                x1="167"
                y1="140"
                x2="183"
                y2="140"
                stroke="#FFFFFF"
                strokeWidth="1"
                strokeLinecap="round"
              />
            </g>

            {/* 3. Sound wave indicators - White color for animation (outer side only) */}
            <g clipPath="url(#rightEarWaveClip)">
              <circle
                className="sound-wave-1"
                cx="175"
                cy="130"
                r="12"
                fill="none"
                stroke="#FFFFFF"
                strokeWidth="1.5"
                opacity="0"
              />
              <circle
                className="sound-wave-2"
                cx="175"
                cy="130"
                r="16"
                fill="none"
                stroke="#FFFFFF"
                strokeWidth="1.5"
                opacity="0"
              />
              <circle
                className="sound-wave-3"
                cx="175"
                cy="130"
                r="20"
                fill="none"
                stroke="#FFFFFF"
                strokeWidth="1.5"
                opacity="0"
              />
            </g>

            {/* 5. LED indicator - Tech detail */}
            <circle
              className="ear-led"
              cx="175"
              cy="108"
              r="2"
              fill="#5046e5"
              opacity="0.8"
            />

            {/* 6. Highlight for depth and dimension */}
            <ellipse
              className="ear-highlight"
              cx="180"
              cy="120"
              rx="4"
              ry="7"
              fill="#FFFFFF"
              opacity="0.4"
            />
          </g>

          {/* Visor/Face plate */}
          <rect
            className="visor"
            x="45"
            y="95"
            width="110"
            height="65"
            rx="30"
            ry="30"
          />

          {/* LEFT EYE - Complete anatomical structure */}
          <g className="left-eye">
            {/* 1. Sclera (Eye white background) */}
            <circle className="sclera" cx="75" cy="127" r="20" />

            {/* 2. Sclera shadow for depth (at edges) */}
            <circle className="sclera-shadow" cx="75" cy="127" r="19" />

            {/* 3. Movable pupil group (animated with eye-look) */}
            <g className="pupil-group" clipPath="url(#leftEyeClip)">
              {/* 3a. Iris glow (outer glow around iris for depth) - moves with iris */}
              <circle className="iris-glow" cx="75" cy="127" r="12" />

              {/* 3b. Iris (colored part with radial gradient) */}
              <circle className="iris" cx="75" cy="127" r="9.5" />

              {/* 3c. Pupil (black center, dilates with emotion) */}
              <circle className="pupil" cx="75" cy="127" r="4.5" />

              {/* 3d. Cornea highlight (main glossy reflection) */}
              <circle className="cornea" cx="72.5" cy="124" r="3.5" />

              {/* 3e. Secondary eye shine/catchlight (spark of life) */}
              <ellipse
                className="eye-shine"
                cx="77"
                cy="129.5"
                rx="2"
                ry="2.5"
              />
            </g>

            {/* 4. Eyelid (for blinking animation) */}
            <ellipse className="eyelid" cx="75" cy="127" rx="20" ry="20" />
          </g>

          {/* RIGHT EYE - Complete anatomical structure */}
          <g className="right-eye">
            {/* 1. Sclera (Eye white background) */}
            <circle className="sclera" cx="125" cy="127" r="20" />

            {/* 2. Sclera shadow for depth (at edges) */}
            <circle className="sclera-shadow" cx="125" cy="127" r="19" />

            {/* 3. Movable pupil group (animated with eye-look) */}
            <g className="pupil-group" clipPath="url(#rightEyeClip)">
              {/* 3a. Iris glow (outer glow around iris for depth) - moves with iris */}
              <circle className="iris-glow" cx="125" cy="127" r="12" />

              {/* 3b. Iris (colored part with radial gradient) */}
              <circle className="iris" cx="125" cy="127" r="9.5" />

              {/* 3c. Pupil (black center, dilates with emotion) */}
              <circle className="pupil" cx="125" cy="127" r="4.5" />

              {/* 3d. Cornea highlight (main glossy reflection) */}
              <circle className="cornea" cx="122.5" cy="124" r="3.5" />

              {/* 3e. Secondary eye shine/catchlight (spark of life) */}
              <ellipse
                className="eye-shine"
                cx="127"
                cy="129.5"
                rx="2"
                ry="2.5"
              />
            </g>

            {/* 4. Eyelid (for blinking animation) */}
            <ellipse className="eyelid" cx="125" cy="127" rx="20" ry="20" />
          </g>
        </StyledUnpodLogo>
      </StyledOrbitLogo>
    </StyledOrbitContainer>
  );
};

export default UnpodLogoAnimation;
