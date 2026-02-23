import React, {ReactNode} from 'react';
import {DefaultTreeAdapterMap, parseFragment} from 'parse5';
import convertAttr from './react-attr-converter';
import styleParser from './style-parser';

type Node = DefaultTreeAdapterMap['node'];
type Element = DefaultTreeAdapterMap['element'];
type TextNode = DefaultTreeAdapterMap['textNode'];
type CommentNode = DefaultTreeAdapterMap['commentNode'];
type DocumentFragment = DefaultTreeAdapterMap['documentFragment'];

type ElementAttrs = {
  key: number;
  dangerouslySetInnerHTML?: { __html: string };

  [key: string]: unknown;
};

const renderNode = (node: Node, key: number): ReactNode => {
  if (node.nodeName === '#text') {
    return (node as TextNode).value;
  }

  if (node.nodeName === '#comment') {
    return (node as CommentNode).data;
  }

  const element = node as Element;
  const attr = element.attrs.reduce<ElementAttrs>(
    (result, attrItem) => {
      const name = convertAttr(attrItem.name);
      result[name] =
        name === 'style' ? styleParser(attrItem.value) : attrItem.value;
      return result;
    },
    {key},
  );

  if (element.childNodes.length === 0) {
    return React.createElement(element.tagName, attr);
  }

  if (element.nodeName === 'script') {
    const textNode = element.childNodes[0] as TextNode;
    attr.dangerouslySetInnerHTML = {__html: textNode.value};
    return React.createElement('script', attr);
  }

  const children = element.childNodes.map((childNode, index) =>
    renderNode(childNode, index),
  );
  return React.createElement(element.tagName, attr, children);
};

const renderHTML = (html: string): ReactNode | ReactNode[] | null => {
  const htmlAST = parseFragment(html) as DocumentFragment;

  if (htmlAST.childNodes.length === 0) {
    return null;
  }

  const result = htmlAST.childNodes.map((node, index) =>
    renderNode(node, index),
  );

  return result.length === 1 ? result[0] : result;
};

export default renderHTML;
