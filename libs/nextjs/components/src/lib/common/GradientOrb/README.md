# GradientOrb Component

A beautiful animated gradient orb component inspired by modern glassmorphism design. Perfect for decorative backgrounds, hero sections, and adding visual interest to your UI.

## Import

```javascript
import GradientOrb from '@unpod/components/common/GradientOrb';
```

## Basic Usage

```jsx
// Simple gradient orb
<GradientOrb />

// Custom size and color variant
<GradientOrb
  size="400px"
  variant="blue"
/>

// Positioned absolutely as background decoration
<div style={{ position: 'relative', overflow: 'hidden' }}>
  <GradientOrb
    position="absolute"
    top="-100px"
    right="-100px"
    size="500px"
    variant="cyan"
    zIndex={0}
  />
  <div style={{ position: 'relative', zIndex: 1 }}>
    {/* Your content here */}
  </div>
</div>
```

## Props

| Prop               | Type          | Default      | Description                                         |
|--------------------|---------------|--------------|-----------------------------------------------------|
| `size`             | string        | `'300px'`    | Width and height of the orb (e.g., '200px', '50vh') |
| `variant`          | string        | `'purple'`   | Color scheme: 'purple', 'blue', 'cyan', 'pink'      |
| `blur`             | string        | `'40px'`     | Amount of blur applied to the gradient              |
| `opacity`          | number        | `0.6`        | Opacity of the orb (0-1)                            |
| `animate`          | boolean       | `true`       | Enable/disable floating animation                   |
| `duration`         | string        | `'10s'`      | Duration of the floating animation                  |
| `rotationDuration` | string        | `'20s'`      | Duration of the internal gradient rotation          |
| `position`         | string        | `'relative'` | CSS position property                               |
| `top`              | string        | -            | CSS top position (e.g., '0', '-50px')               |
| `bottom`           | string        | -            | CSS bottom position                                 |
| `left`             | string        | -            | CSS left position                                   |
| `right`            | string        | -            | CSS right position                                  |
| `zIndex`           | number/string | -            | CSS z-index                                         |
| `className`        | string        | -            | Additional CSS class                                |
| `style`            | object        | -            | Inline styles                                       |

## Examples

### Multiple Orbs Background

```jsx
<div style={{ position: 'relative', minHeight: '100vh', overflow: 'hidden' }}>
  <GradientOrb
    position="absolute"
    top="-150px"
    left="-150px"
    size="600px"
    variant="purple"
    opacity={0.4}
    zIndex={0}
  />
  <GradientOrb
    position="absolute"
    bottom="-100px"
    right="-100px"
    size="500px"
    variant="cyan"
    opacity={0.3}
    duration="15s"
    zIndex={0}
  />
  <GradientOrb
    position="absolute"
    top="50%"
    left="50%"
    size="400px"
    variant="pink"
    opacity={0.2}
    duration="20s"
    zIndex={0}
  />

  <div style={{ position: 'relative', zIndex: 1 }}>
    {/* Your page content */}
  </div>
</div>
```

### Hero Section with Gradient Orb

```jsx
<div style={{ position: 'relative', padding: '100px 20px' }}>
  <GradientOrb
    position="absolute"
    top="0"
    right="0"
    size="600px"
    variant="blue"
    opacity={0.5}
    zIndex={0}
  />
  <div style={{ position: 'relative', zIndex: 1, textAlign: 'center' }}>
    <h1>Welcome to Our Platform</h1>
    <p>Experience the future of social communication</p>
  </div>
</div>
```

### Static Decoration (No Animation)

```jsx
<GradientOrb
  size="200px"
  variant="purple"
  animate={false}
  blur="30px"
/>
```

## Color Variants

- **purple** (default): Purple to blue gradient with warm tones
- **blue**: Cool blue gradient with lighter tones
- **cyan**: Cyan to blue gradient with fresh tones
- **pink**: Pink to purple gradient with warm tones

## Tips

1. Use `position="absolute"` with `overflow: 'hidden'` on the parent for background decorations
2. Layer multiple orbs with different sizes and opacities for depth
3. Lower opacity values (0.2-0.4) work best for subtle backgrounds
4. Increase blur for softer, more ambient effects
5. Set `zIndex={0}` to keep orbs behind content
6. Disable animation (`animate={false}`) if you need static decorations
