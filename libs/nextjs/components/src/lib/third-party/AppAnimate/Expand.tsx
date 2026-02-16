import React, { Component } from 'react';
import PropTypes from 'prop-types';

// In firefox, setTimeout with duration 0 too short for browser notice the changes in dom
const initialTransitDuration = 20;

const PHASE = {
  CLOSE: 'close',
  CLOSING: 'closing',
  CLOSED: 'closed',
  OPEN: 'open',
  OPENING: 'opening',
  OPENED: 'opened',
};

const GROUP = {
  [PHASE.CLOSE]: PHASE.CLOSE,
  [PHASE.CLOSED]: PHASE.CLOSE,
  [PHASE.OPENING]: PHASE.CLOSE,

  [PHASE.CLOSING]: PHASE.OPEN,
  [PHASE.OPEN]: PHASE.OPEN,
  [PHASE.OPENED]: PHASE.OPEN,
};

class Expand extends Component {
  constructor(props) {
    super(props);
    this.state = {
      status: this.props.open ? PHASE.OPEN : PHASE.CLOSE,
    };
  }

  componentDidUpdate(prevProps /* prevState */) {
    if (prevProps.open !== this.props.open) {
      this.toggle(this.props.open);
    }
  }

  componentWillUnmount() {
    this.clearDelay();
  }

  getClientHeight = () => this.refWrapper.scrollHeight;

  getDefaultExpandStyle = () => {
    const { status } = this.state;

    switch (status) {
      case PHASE.OPENING:
      case PHASE.CLOSE:
      case PHASE.CLOSED:
        return { height: 0, opacity: 0, overflow: 'hidden' };
      case PHASE.OPENED:
      case PHASE.CLOSING:
        return {
          height: this.getClientHeight(),
          opacity: 1,
          overflow: 'hidden',
        };
      default:
        return { height: 'auto', opacity: 1, overflow: 'unset' };
    }
  };

  getExpandStyle = () => ({
    ...this.getDefaultExpandStyle(),
    ...this.props.styles[GROUP[this.state.status]],
  });

  getTransition = (attribute) =>
    `${attribute} ${this.props.duration}ms ${this.props.easing}`;

  getStyle() {
    const transition = this.props.transitions.map(this.getTransition).join(',');

    return {
      ...this.getExpandStyle(),
      transition,
    };
  }

  updateStatus = (status) => this.setState({ status });

  delay = (fn, time) => {
    this.timeout = setTimeout(fn, time);
  };

  clearDelay = () => {
    if (this.timeout) {
      clearTimeout(this.timeout);
    }
  };

  transit = (entering, entered, enter) => {
    const { duration } = this.props;

    this.updateStatus(entering);

    this.delay(() => {
      this.updateStatus(entered);

      this.delay(() => {
        this.updateStatus(enter);
      }, duration);
    }, initialTransitDuration);
  };

  toggle = (open) => {
    this.clearDelay();

    if (open) {
      this.transit(PHASE.OPENING, PHASE.OPENED, PHASE.OPEN);
    } else {
      this.transit(PHASE.CLOSING, PHASE.CLOSED, PHASE.CLOSE);
    }
  };

  setRef = (ref) => {
    this.refWrapper = ref;
  };

  render() {
    const { className, children, tag: Tag } = this.props;

    const childProps = {
      className,
      style: this.getStyle(),
      ref: this.setRef,
    };

    return <Tag {...childProps}>{children}</Tag>;
  }
}

Expand.propTypes = {
  children: PropTypes.node,
  open: PropTypes.bool,
  duration: PropTypes.number,
  easing: PropTypes.string,
  className: PropTypes.string,
  tag: PropTypes.string,
  transitions: PropTypes.arrayOf(PropTypes.string),
  styles: PropTypes.shape({
    [PHASE.OPEN]: PropTypes.object,
    [PHASE.CLOSE]: PropTypes.object,
  }),
};

Expand.defaultProps = {
  open: false,
  duration: 200,
  easing: 'ease-in-out',
  className: '',
  tag: 'div',
  transitions: ['height', 'opacity'],
  styles: {},
};

export default Expand;
