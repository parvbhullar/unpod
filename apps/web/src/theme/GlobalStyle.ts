'use client';
import { createGlobalStyle } from 'styled-components';

export const GlobalStyles = createGlobalStyle`
  html {
    scrollbar-width: thin;
    --media-icon-color: #fff;
    font-family: ${({ theme }) => theme.font.family};
  }
  body {
    margin: 0 !important;
  }

  #__next {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
    min-width: 0;
    width: 100%;
    height: auto;
    --media-icon-color: #fff;
  }

  svg {
    vertical-align: middle;
  }

  pre, code, kbd, samp {
    font-family: ${({ theme }) => theme.font.family};
  }

  img, table, iframe {
    max-width: 100%;
    height: auto;
  }

  a,
  a:active,
  a:visited {
    text-decoration: none;
  }

  h1, h2, h3, h4, h5, h6 {
    // color: ${({ theme }) => theme?.palette.text.dark} !important;
  }

  .ant-carousel.auth-slider  {
    .slick-dots {
      justify-content: flex-end;
      margin-right: 20px;

      li {
        width: 8px;
        height: 8px;

        button {
          height: 8px;
          border-radius: 50%;
          opacity: 1;
        }

        &.slick-active {
          width: 40px;

          button {
            border-radius: 12px;
            background-color: #796CFF;
          }
        }
      }
    }

    .slick-dots-bottom {
      bottom: 30px;
    }
  }

  .trigger {
    font-size: 24px;
  }

  .text-center {
    text-align: center;
  }

  .font-weight-normal {
    font-weight: normal !important;
  }

  .mb-0 {
    margin-bottom: 0 !important;
  }

  .h-100 {
    height: 100%;
  }

  .ant-layout-header {
    //height: 84px !important;
  }

  .ant-form-item-explain-error {
    margin-bottom: 16px;
  }

  /*.ant-btn.ant-btn-sm {
    font-size: 14px;
  }*/

  #videos{
    position: relative;
    height: 85vh;
    width: 100vw;
    margin: auto;
    align-self: flex-start;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(440px, 1fr));
    justify-items: center;
    align-items: center;
  }

  .vid{
    position: relative;
    background-color:black;
    border-width: 1px;
    border-color: #38373A;
    border-style: solid;
  }

  .controls{
    position: absolute;
    bottom: -10px;
    left: 50%;
    transform: translateX(-50%);
    margin: -20px auto;
    display: grid;
    grid-template-columns: repeat(3, 33%);
    align-items: center;
    justify-items: center;
    z-index: 1;
    width: 500px;
    max-width: 60vw;
  }

  .controls p{
    padding: 10px;
    cursor: pointer;
    background: #38373A;
    color: #F7F7F7;
    border-width: 1px;
    border-color: #F7F7F7;
    border-style: solid;
  }

  .controls p.on{
    background: #F7F7F7;
    color: #38373A;
    border-width: 1px;
    border-color: #38373A;
    border-style: solid;
  }

  .join{
    position: absolute;
    z-index: 1;
    // width: 30vw;
    height: fit-content;
    // height: -moz-max-content;
    top: 50vh;
    left: 50vw;
    transform: translate(-50%, -50%);
    width: 500px;
    max-width: 75vw;
  }

  .join  input{
    padding: 15px;
    font-size: 1rem;
    border-width: 1px;
    border-color: #38373A;
    border-style: solid;
    width: 80%;
    display: block;
    margin:  50px auto;
  }

  .join  button{
    min-width: 200px;
    padding: 12px 0;
    text-align: center;
    background-color: #38373A;
    color: #F7F7F7;
    border-width: 1px;
    border-color: #F7F7F7;
    border-style: solid;
    font-size: 1rem;
    font-weight: 400;
    cursor: pointer;
    display: block;
    margin: 0 auto;
  }

  @keyframes dot-flashing {
    0% {
      background-color: ${({ theme }) => theme?.palette.primary};
    }
    50%, 100% {
      background-color: rgba(152, 128, 255, 0.3);
    }
  }

  .badge-info {
    border-color: ${({ theme }) => theme.palette.info}!important;
    color: ${({ theme }) => theme.palette.info};
    background-color: ${({ theme }) => theme.palette.info + '22'};
  }

  .badge-success {
    border-color: ${({ theme }) => theme.palette.success}!important;
    color: ${({ theme }) => theme.palette.success};
    background-color: ${({ theme }) => theme.palette.success + '22'};
  }

  .badge-warning {
    border-color: ${({ theme }) => theme.palette.warning}!important;
    color: ${({ theme }) => theme.palette.warning};
    background-color: ${({ theme }) => theme.palette.warning + '22'};
  }

  .badge-error {
    border-color: ${({ theme }) => theme.palette.error}!important;
    color: ${({ theme }) => theme.palette.error};
    background-color: ${({ theme }) => theme.palette.error + '22'};
  }

  .badge-primary {
    border-color: ${({ theme }) => theme.palette.primary}!important;
    color: ${({ theme }) => theme.palette.primary};
    background-color: ${({ theme }) => theme.palette.primary + '22'};
  }

  .text-capitalize {
    text-transform: capitalize;
  }
`;
