// import React, { Fragment } from 'react';
// import PropTypes from 'prop-types';
// // import dynamic from 'next/dynamic';
// import ToolbarFormats from '../ToolbarOptions';
// import { StyledAppEditor, StyledToolbar } from './index.styled';
// import { Tooltip } from 'antd';
// import clsx from 'clsx';
// import ReactQuill, { Quill } from 'react-quill';
// import MagicUrl from 'quill-magic-url';
//
// Quill.register('../../../../modules/magicUrl', MagicUrl);
//
// /*const ReactQuill = dynamic(import('react-quill'), {
//   ssr: false,
//   loading: () => <p>Loading ...</p>,
// });*/
//
// /*const Embed = Quill.import('blots/block/embed');
//
// class Hr extends Embed {
//   static create(value) {
//     return super.create(value);
//   }
// }
//
// Hr.blotName = 'hr'; //now you can use .ql-hr classname in your toolbar
// Hr.className = 'ql-custom-hr';
// Hr.tagName = 'hr';
//
// function customHrHandler() {
//   // get the position of the cursor
//   const cursorPosition = this.quill.getLength();
//   this.quill.insertEmbed(cursorPosition, 'hr', 'null');
// }
//
// Quill.register({
//   'formats/hr': Hr,
// });*/
//
// export const toolbarSelectBox = (formatData) => {
//   const { className, options } = formatData;
//   return (
//     <select className={`ql-${className}`} onChange={(e) => e.persist()}>
//       <option selected />
//       {options.map((value, index) => {
//         return <option value={value} key={'option-' + index} />;
//       })}
//     </select>
//   );
// };
// export const toolbarButton = (formatData) => {
//   const { className, value, tooltip } = formatData;
//   return (
//     <Tooltip title={tooltip}>
//       <button className={`ql-${className}`} value={value} />
//     </Tooltip>
//   );
// };
//
// const AppEditorInput = ({
//   toolbarId,
//   options,
//   theme,
//   visible,
//   noToolbar,
//   ...rest
// }) => {
//   // console.log('AppEditorInput Rest Props: ', rest);
//   return (
//     <StyledAppEditor>
//       <ReactQuill
//         modules={{
//           ...options,
//           toolbar: {
//             container: toolbarId ? `#${toolbarId}` : null,
//             /*handlers: {
//               hr: customHrHandler,
//             },*/
//           },
//           magicUrl: {
//             // Regex used to check URLs during typing
//             urlRegularExpression: /(https?:\/\/[\S]+)|(www.[\S]+)|(tel:[\S]+)/g,
//             // Regex used to check URLs on paste
//             globalRegularExpression: /(https?:\/\/|www\.|tel:)[\S]+/g,
//           },
//         }}
//         theme={theme}
//         {...rest}
//       />
//
//       {!noToolbar && toolbarId && (
//         <StyledToolbar
//           id={toolbarId}
//           className={clsx({ 'theme-snow': theme === 'snow' })}
//           style={{
//             visibility: visible ? 'visible' : 'hidden',
//             height: visible ? 'auto' : 0,
//             padding: visible && theme === 'snow' ? '8px' : 0,
//             marginTop: visible && theme === 'snow' ? '16px' : 0,
//           }}
//         >
//           <span className="ql-formats">
//             {ToolbarFormats.map((format, index) => (
//               <Fragment key={index}>
//                 {format?.options
//                   ? toolbarSelectBox(format, index)
//                   : toolbarButton(format, index)}
//               </Fragment>
//             ))}
//           </span>
//         </StyledToolbar>
//       )}
//     </StyledAppEditor>
//   );
// };
//
// AppEditorInput.propTypes = {
//   toolbarId: PropTypes.string,
//   placeHolder: PropTypes.string,
//   options: PropTypes.object,
//   theme: PropTypes.string,
//   visible: PropTypes.bool,
//   noToolbar: PropTypes.bool,
// };
//
// AppEditorInput.defaultProps = {
//   placeHolder: 'Enter your text here',
//   theme: 'bubble',
//   visible: true,
// };
//
// export default AppEditorInput;
import React from 'react';

const Index = () => {
  return <div></div>;
};

export default Index;
